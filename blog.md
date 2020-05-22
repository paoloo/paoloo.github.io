---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: page
title: Blog
permalink: /blog/
---
<main class="container">
  <div class="row">
    <div class="col-2">
      <br/>
      {% for post in site.posts %}
        <div class="post-meta" style="color:#000;">{{ post.date | date: '%B %d, %Y' }}  <div style="color:#c0c0c0;font-size: 11px;">{{ post.tags | join:", " }}</div> </div>
        <a class="post-link" href="{{ post.url }}">{{ post.title }}</a>
        <p class="post-meta">{{ post.content | strip_html | truncatewords: 50 }}
          <a class="post-link" href="{{ site.baseurl }}/{{ post.url }}" style="font-size: 14px;text-align:right;">[ Read more ]</a>
        </p>
      <br/>
      {% endfor %}
    </div>
  </div>
</main>
