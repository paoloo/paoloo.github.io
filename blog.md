---
layout: page
title: Blog
permalink: /blog/
---

<style>
@font-face {
    font-family: 'Oxanium';
    src: url('{{ site.url }}/res/Oxanium.ttf');
}
</style>
<main class="container">
  <div class="row">
    <div class="col-2">
      <br/>
      {% for post in site.posts %}
        <div class="post-meta" style="color:#f3980b;">{{ post.date | date: '%B %d, %Y' }}  <div style="color:#c0c0c0;font-size: 11px;">{{ post.tags | join:", " }}</div> </div>
        <a class="post-link" href="{{ post.url }}" style="text-shadow: 3px 0px 5px rgba(255,0,255,0.7), -3px 0px 5px rgba(50,50,255,1); font-family: Oxanium, sans-serif;">{{ post.title }}</a>
        <p class="post-meta">{{ post.content | strip_html | truncatewords: 50 }}
          <a class="post-link" href="{{ post.url }}" style="font-size: 14px;text-align:right;text-shadow: 3px 0px 5px rgba(255,0,255,0.7), -3px 0px 5px rgba(50,50,255,1);">[ Read more ]</a>
        </p>
      <br/>
      {% endfor %}
    </div>
  </div>
</main>
