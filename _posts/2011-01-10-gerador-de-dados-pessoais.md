---
title: Gerador de Dados Pessoais
date: 2011-01-10T11:49:00+00:00
author: paolo
layout: post
permalink: /2011/01/10/gerador-de-dados-pessoais/
tagazine-media:
  - 'a:7:{s:7:"primary";s:0:"";s:6:"images";a:0:{}s:6:"videos";a:0:{}s:11:"image_count";s:1:"0";s:6:"author";s:8:"13279106";s:7:"blog_id";s:8:"15967288";s:9:"mod_stamp";s:19:"2011-01-13 17:49:44";}'
categories:
  - pt-BR
tags:
  - hacks
  - random
---
Eu sempre vejo geradores de todo tipo de coisa poraí, mas quando voce precisa fazer cadastros imbecis em sites aleatórios, sempre tem aquele delay mental para criar dados fakes(afinal, voce nao vai sair dando suas informacoes pessoals para todo lugar na internet ne?). Assim sendo, baseando-me num gerador gringo, fiz uma versão nacional do Gerador de Dados Pessoais.

<pre class="brush: python; title: ; notranslate" title="">from random import randint,uniform
from string import lower,upper
from math import sqrt
alfanum = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
email = ['yahoo.com.br', 'hotmail.com', 'gmail.com', 'bol.com.br', 'terra.com.br', 'globo.com', 'ig.com.br']
emailsep = ['.','','_','-']
empregos = [['professor', 'motorista', 'gari', 'mecanico', 'engenheiro', 'advogado', 'desempregado', 'medico', 'empresario', 'enfermeiro', 'vendedor', 'bancario', 'estudante', 'taxista', 'gerente de vendas', 'cozinheiro', 'gogo-boy', 'programador', 'politico', 'animador', 'digitador'] , ['professora', 'motorista', 'gari', 'domestica', 'engenheira', 'advogada', 'desempregada', 'medica', 'empresaria', 'enfermeira', 'vendedora', 'bancaria', 'estudante', 'taxista', 'gerente de vendas', 'cozinheira', 'jornalista', 'prostituta', 'politica', 'animadora', 'digitadora']]
nomes = [['JOAO', 'LUCAS', 'GABRIEL', 'MATHEUS', 'PEDRO', 'LUIZ', 'JOSE', 'GUILHERME', 'CARLOS', 'RAFAEL', 'FELIPE', 'BRUNO', 'GUSTAVO', 'PAULO', 'MARCOS', 'LEONARDO', 'VINICIUS', 'DANIEL', 'LUIS', 'THIAGO', 'MATIAS', 'RICARDO', 'ALFREDO', 'ALESSANDRO'], ['MARIA', 'ANA', 'JULIA', 'LETICIA', 'LARISSA', 'BEATRIZ', 'JESSICA', 'BRUNA', 'AMANDA', 'GABRIELA', 'LUANA', 'SAMANTA', 'MAYARA', 'SAMARA', 'JAQUELINE', 'RACHEL', 'RAQUEL', 'LUCIA', 'DENISE', 'DANIELA', 'ERICA']]
sobrenomes = ['ABREU', 'ALVES', 'ALBINO', 'ALMEIDA', 'AMARAL', 'ARAUJO', 'ANDRADE', 'ANTUNES', 'AZEVEDO', 'ASSIS', 'BARRETO', 'BARROS', 'BAHR', 'BATISTA', 'BENTO', 'BRASIL', 'BRAGA', 'BRITO', 'CAMARGO', 'CAMPOS', 'CARDOSO', 'CANDIDO', 'CARVALHO', 'CASTRO', 'CHAGAS', 'COELHO', 'CORREIA', 'DUTRA', 'FAGUNDES', 'FERNANDES', 'FRAGA', 'FRANCA', 'FREITAS', 'JUSTINO', 'LEAL', 'LEITE', 'LIMA', 'LINHARES', 'LOPES', 'MACHADO', 'MACEDO', 'MACIEL', 'MARTINS', 'MATOS', 'MARQUES', 'MEDEIROS', 'MIRANDA', 'MORAES', 'MONTEIRO', 'NASCIMENTO', 'NEVES', 'OLIVEIRA', 'ONOFRE', 'PACHECO', 'PADILHA', 'PAIVA', 'PEREIRA', 'PESSOA', 'PINHO', 'PINTO', 'PIRES', 'PRADO', 'RABELO', 'RAMOS', 'RIBEIRO', 'ROCHA', 'RODRIGUES', 'ROSA', 'SALES', 'SABINO', 'SANTOS', 'SILVA', 'SILVEIRA', 'SOARES', 'TEIXEIRA', 'VARGAS', 'VASCONCELOS', 'VIEIRA', 'XAVIER']
sexo = ['M','F']
sangueT = ['A','B','AB','O']
sangueF = ['+','-']
logradouro = ['RUA','AVENIDA','TRAVESSA','ALAMEDA','PRACA']
ruas = ['PROFESSOR','DOUTOR','MAJOR','TIPOGRAFO','','DESEMBARGADOR','SARGENTO']
slDDD=['68', '82', '96', '92', '97', '71', '73', '74', '75', '77', '85', '88', '61', '27', '28', '62', '64', '98', '99', '65', '66', '67', '31', '32', '33', '34', '35', '37', '38', '91', '93', '94', '83', '41', '42', '43', '44', '45', '46', '81', '87', '86', '89', '21', '22', '24', '24', '84', '51', '53', '54', '55', '69', '95', '47', '48', '49', '11', '12', '13', '14', '15', '16', '17', '18', '19', '79', '63']
lsDDD= {  '68': ['AC','Rio Branco'],  '82': ['AL','Maceio'],  '96': ['AP','Macapa'],  '92': ['AM','Manaus'],  '97': ['AM','Interior'],  '71': ['BA','Salvador'],  '73': ['BA','Ilheus'],  '74': ['BA','Juazeiro'],  '75': ['BA','Feira de Santana'],  '77': ['BA','Vitoria da Conquista'],  '85': ['CE','Fortaleza'],  '88': ['CE','Interior'],  '61': ['DF','Brasilia'],  '27': ['ES','Vitoria'],  '28': ['ES','Interior'],  '62': ['GO','Goiania'],  '64': ['GO','Interior'],  '98': ['MA','Sao Luis'],  '99': ['MA','Interior'],  '65': ['MT','Cuiaba'],  '66': ['MT','Interior'],  '67': ['MA','Campo Grande'],  '31': ['MG','Belo Horizonte'],  '32': ['MG','Juiz de Fora'],  '33': ['MG','Gov Valadares'],  '34': ['MG','Uberlandia'],  '35': ['MG','P. de Caldas'],  '37': ['MG','Divinopolis'],  '38': ['MG','Montes Claros'],  '91': ['PA','Belem'],  '93': ['PA','Santarem'],  '94': ['PA','Maraba'],  '83': ['PB','Joao Pessoa'],  '41': ['PR','Curitiba'],  '42': ['PR','Ponta Grossa'],  '43': ['PR','Londrina'],  '44': ['PR','Maringa'],  '45': ['PR','Foz do Iguacu'],  '46': ['PR','Fco Beltrao'],  '81': ['PE','Recife'],  '87': ['PE','Interior'],  '86': ['PI','Teresina'],  '89': ['PI','Interior'],  '21': ['RJ','Rio de Janeiro'],  '22': ['RJ','C. dos Goytacazes'],  '24': ['RJ','Volta Redonda'],  '24': ['RJ','Petropolis'],  '84': ['RN','Natal'],  '51': ['RS','Porto Alegre'],  '53': ['RS','Pelotas'],  '54': ['RS','Caxias do Sul'],  '55': ['RS','Santa Maria'],  '69': ['RO','Porto Velho'],  '95': ['RR','Boa Vista'],  '47': ['SC','Joinville'],  '48': ['SC','Florianopolis'],  '49': ['SC','Chapeco'],  '11': ['SP','Sao Paulo'],  '12': ['SP','Sao Jose dos Campos'],  '13': ['SP','Santos'],  '14': ['SP','Bauru'],  '15': ['SP','Sorocaba'],  '16': ['SP','Ribeirao Preto'],  '17': ['SP','Sao Jose do Rio Preto'],  '18': ['SP','Presidente Prudente'],  '19': ['SP','Campinas'],  '79': ['SE','Aracaju'],  '63': ['TO','Palmas'],}
def calcCPF(num):
  somatorio = 0
  qtde = (len(num)+1)
  for i in xrange(qtde-1):
    somatorio += (num[i]*(qtde-i))
  resto = 11-(somatorio % 11)
  if resto &lt; 10: return resto
  return 0

def getCPF():
  n = [randint(0,9) for i in xrange(9)]
  n.append(calcCPF(n))
  n.append(calcCPF(n))
  n.insert(3,'.')
  n.insert(7,'.')
  n.insert(11,'-')
  mm = ''.join([str(n[j]) for j in xrange(14)])
  return mm

def calcCC(num):
  somatorio = 0
  for i in range(len(num)):
    if ((i+1)%2==0):
      somatorio+=num[i]
    else:
      if ((num[i]*2)&gt;9): somatorio += (2*num[i]-9)
      else: somatorio += (2*num[i])
  if ((somatorio%10)==0): return 0
  else: return (10-(somatorio%10))

def getCC():
  n = [randint(0,9) for i in xrange(15)]
  n[0] = randint(3,6)
  n.append(calcCC(n))
  n.insert(4,'.')
  n.insert(9,'.')
  n.insert(14,'.')
  mm = ''.join([str(n[j]) for j in xrange(19)])
  return mm

genero = randint(0,1)
ddd=slDDD[randint(0,len(slDDD)-1)]
nomec = '%s %s' % ( ' '.join([nomes[genero][randint(0 ,len(nomes[genero])-1)] for k in xrange(randint(1,2))]) , ' '.join([sobrenomes[randint(0,len(sobrenomes)-1)] for k in xrange(randint(1,3))]) )
print nomec
print '%s %s %s %s, %s' % ( logradouro[randint(0,len(logradouro)-1)],ruas[randint(0,len(ruas)-1)],nomes[0][randint(0,len(nomes[0])-1)],sobrenomes[randint(0,len(sobrenomes)-1)], str(randint(1,999)) )
cep = [str(randint(0,9)) for k in xrange(8)]
cep.insert(2,'.')
cep.insert(6,'-')
print '%s, %s, %s' % (upper(lsDDD[ddd][1]),lsDDD[ddd][0],''.join(cep))
print '\tTelefone: (%s)%s-%s' % (ddd,''.join([str(randint(0,9)) for k in xrange(4)]),''.join([str(randint(0,9)) for k in xrange(4)]))
print '\tSexo: %s' % sexo[genero]
print '\tCPF: %s' % getCPF()

def genrg():
  rg = [randint(0,9) for i in range(8)]
  soma = sum([(2+i)*rg[i] for i in range(8)])
  rg = ''.join([str(x) for x in rg])
  for dv in range(10):
    if (soma + dv*100) % 11 == 0:
      break
  return rg + str(dv)

print '\tRG: %s SSP %s' % (genrg(),lsDDD[ddd][0])
print '\tData de Nascimento: %s/%s/%s' % (randint(1,30),randint(1,12),randint(1960,1999))
print '\tMae: %s %s' % ( ' '.join([nomes[1][randint(0 ,len(nomes[1])-1)] for k in xrange(randint(1,2))]) , ' '.join([sobrenomes[randint(0,len(sobrenomes)-1)] for k in xrange(randint(1,3))]) )
print '\tSangue: %s%s' % (sangueT[randint(0,len(sangueT)-1)],sangueF[randint(0,1)])
zimeiu = nomec.split(' ')
zumeiu = '%s%s%s@%s' % (zimeiu[0],emailsep[randint(0,len(emailsep)-1)],''.join([zimeiu[k][0] for k in range(1,len(zimeiu))]),email[randint(0,len(email)-1)])
zumeiu=lower(zumeiu)
print '\tEmail: %s' % zumeiu
print '\tSenha: %s' % ''.join([alfanum[randint(0,len(alfanum)-1)] for k in xrange(randint(4,11))])
print '\tCartao de Credito: %s' % getCC()
print '\tcvv: %s' % str(randint(100,999))
imc = uniform(19,29)
peso = uniform(42,89)
altura = sqrt(peso/imc)
print '\tpeso: %.2f kg' % peso
print '\taltura: %.2f m' % altura
print '\tEmprego: %s' % empregos[genero][randint(0,len(empregos[0])-1)]
</pre>

É bem divertido(e nada útil LOL) e várias vezes esbarrei em gente que realmente existe.  
Exemplo de saida:

<pre class="brush: plain; title: ; notranslate" title="">$ python g.py
PEDRO RODRIGUES ANDRADE
AVENIDA DESEMBARGADOR PAULO ALVES, 472
PONTA GROSSA, PR, 54.663-607
	Telefone: (42)9322-7623
	Sexo: M
	CPF: 045.952.937-47
	RG: 387979311 SSP PR
	Data de Nascimento: 25/29/1970
	Mae: GABRIELA JAQUELINE ASSIS CARVALHO ARAUJO
	Sangue: AB+
	Email: pedro-ra@terra.com.br
	Senha: FviqKAxZgP
	Cartao de Credito: 6233.8988.3744.8953
	cvv: 240
	peso: 76.88 kg
	altura: 1.87 m
	Emprego: cozinheiro </pre>

P.S.: Todos os dados são aleatórios, incluindo numeros de CPF, CC e Telefone, eles apenas sao formatados e validados para o padrão correto, podem até existir, mas nao estão definidos em local algum do script.  
P.P.S.: O calculo de validação do RG é o do estado de Sao Paulo pois foi o único cuja descrição foi encontrada(Do Ceará, parece ser sequencial com o ano no início).

o/