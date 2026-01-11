---
title: "Building a Minimal Virtual Machine in Go (and How to Grow It)"
date: 2026-01-11 09:00:00 -0300
author: paolo
layout: post
permalink: /2026/01/11/building-a-small-vm-in-go/
categories:
  - en-US
tags:
  - comp
  - vm
  - go
---

Virtual Machines (VMs) are one of those concepts that look intimidating at first, but become surprisingly approachable once you build a small one yourself. Whether you are implementing a scripting language, an embedded DSL, or a lightweight execution engine, a minimal VM can go a long way.

In this post, I will walk through the **design and implementation of a small stack-based virtual machine**, inspired by, and directly derived from, a VM I previously implemented for another project, available at https://github.com/paoloo/pikaSpeak/blob/main/pika_vm.go

This will (try to) cover:

- Core VM architecture
- Instruction format and execution loop
- Stack and memory model
- Error handling and safety
- How to **extend the VM** with new instructions, control flow, and features

This post is meant to be both **didactic and practical**. You should be able to adapt this VM to your own projects easily.

So, first, why a Stack-Based VM? (no, I'm not a LUA-simp, well, I do like LUA but yeah...)

Before diving into code, it is worth clarifying the design choice.

A **stack-based VM** has simpler instructions, requires less bookkeeping than register-based VMs and is ideal for small interpreters and embedded languages. Overall, for a compact and hackable VM, stack-based is usually the right call.


Alright, a minimal VM usually has:
- an **instruction stream** (bytecode / opcodes)
- an **instruction pointer** (`ip`)
- an **operand stack**
- optional **globals / locals**
- an execution loop: **fetch → decode → execute**

I’ll show everything as a small **stack machine**, because it is the easiest to implement and extend. First, let's define the instructions. A clean way to start is to define an `Opcode` enum and an `Instruction` struct:
```go
type Opcode uint8

const (
    OP_HALT Opcode = iota
    OP_PUSHI      // push immediate int
    OP_ADD
    OP_SUB
    OP_MUL
    OP_DIV
    OP_PRINT
)

type Instruction struct {
    Op  Opcode
    Arg int // used by OP_PUSHI (and later: jumps, loads, calls...)
}
```
Keeping `Arg` as an `int` makes early prototyping easy but we could pack operands into `[]byte` and decode on demand for a more compact bytecode.

Now, regarding the VM state. A minimal VM state for a stack machine is:
```go
type VM struct {
    ip      int
    stack   []int
    program []Instruction
}
```

We can add more state later (globals, heap, call stack, debug flags) if needed. But this covers pretty much all that we need for now.

Now, regarding the stack, the good and bad thing is that most VM bugs are stack bugs. Centralize stack ops:

```go
func (vm *VM) push(v int) { vm.stack = append(vm.stack, v) }

func (vm *VM) pop() int {
    if len(vm.stack) == 0 {
        panic("stack underflow")
    }
    v := vm.stack[len(vm.stack)-1]
    vm.stack = vm.stack[:len(vm.stack)-1]
    return v
}
```

For “real” use, replace `panic` with an error return, and carry location info (`ip`, current opcode). Panic works for my case as it's safe and never breaks.

The next step is the execution loop. This is the VM.

```go
func (vm *VM) Run() {
    for vm.ip >= 0 && vm.ip < len(vm.program) {
        ins := vm.program[vm.ip]

        switch ins.Op {
        case OP_HALT:
            return

        case OP_PUSHI:
            vm.push(ins.Arg)

        case OP_ADD:
            b := vm.pop()
            a := vm.pop()
            vm.push(a + b)

        case OP_SUB:
            b := vm.pop()
            a := vm.pop()
            vm.push(a - b)

        case OP_MUL:
            b := vm.pop()
            a := vm.pop()
            vm.push(a * b)

        case OP_DIV:
            b := vm.pop()
            a := vm.pop()
            vm.push(a / b)

        case OP_PRINT:
            v := vm.pop()
            fmt.Println(v)

        default:
            panic("unknown opcode")
        }

        vm.ip++
    }
}
```

Two important details: the **default** case matters. Unknown bytecode should never silently succeed and `ip++` happens after most instructions. Jumps/calls will override `ip` and `continue`.

Let's test it and build a small program

```go
prog := []Instruction{
    {Op: OP_PUSHI, Arg: 10},
    {Op: OP_PUSHI, Arg: 20},
    {Op: OP_ADD},
    {Op: OP_PRINT},
    {Op: OP_HALT},
}

vm := &VM{program: prog}
vm.Run()
```

Output:

```
30
```

At this point you have a working VM! YAY! But it's just a glorified calculator for now.

Now the fun part: expanding the VM.

Let's start implementing the control flows, unconditional and conditional jumps:

Add the Opcode...
```go
const (
    // ...
    OP_JMP
    OP_JZ  // jump if zero
)
```

and the implementation:

```go
case OP_JMP:
    vm.ip = ins.Arg
    continue

case OP_JZ:
    v := vm.pop()
    if v == 0 {
        vm.ip = ins.Arg
        continue
    }
```

With `OP_JZ`, you can implement `if`, `while`, and simple branching. Really easy.

Now, for global variables, first adding a globals array:

```go
type VM struct {
    ip      int
    stack   []int
    program []Instruction
    globals []int
}
```
and the opcodes...
- `OP_GLOAD <idx>` pushes `globals[idx]`
- `OP_GSTORE <idx>` pops and stores

```go
case OP_GLOAD:
    vm.push(vm.globals[ins.Arg])

case OP_GSTORE:
    vm.globals[ins.Arg] = vm.pop()
```

Which gets you a usable “language core” quickly. The next step is to add a types, because, well, types matter!

ints-only is limiting. Introduce a tagged union:

```go
type Kind uint8

const (
    KInt Kind = iota
    KBool
    KStr
)

type Value struct {
    K Kind
    I int
    B bool
    S string
}
```

Then change the stack to `[]Value` and teach each opcode how to handle types. If we do this, also add explicit type errors (instead of panics) so debugging stays sane-ish.

Now, for the function calls, to support calls/returns we need a **call stack** storing return addresses and optionally stack frames (locals). The minimal approach is:

```go
type VM struct {
    ip        int
    stack     []int
    program   []Instruction
    callstack []int
}
```
And the opcodes:
- `OP_CALL <addr>`: push return ip, then jump
- `OP_RET`: pop return ip, jump back

```go
case OP_CALL:
    vm.callstack = append(vm.callstack, vm.ip+1)
    vm.ip = ins.Arg
    continue

case OP_RET:
    n := len(vm.callstack)
    if n == 0 { panic("callstack underflow") }
    ret := vm.callstack[n-1]
    vm.callstack = vm.callstack[:n-1]
    vm.ip = ret
    continue
```

This was the basic first version of the VM. I expanded it more and you can check the source code to understand it, but everything follows this philosophy.

This text may contain errors and I wrote in portuguese for a class and translated automatically, with a few minor corrections so, yeah.