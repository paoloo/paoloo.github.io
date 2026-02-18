---
layout: sidebar
title: Blog
permalink: /blog/
---

{% for post in site.posts %}
  <div class="post-list-item">
    <div class="post-meta">{{ post.date | date: '%B %d, %Y' }}</div>
    <div class="post-tags">{{ post.tags | join: ", " }}</div>
    <a class="post-link" href="{{ post.url }}" style="text-shadow: 3px 0px 5px rgba(255,0,255,0.7), -3px 0px 5px rgba(50,50,255,1); font-family: Oxanium, sans-serif;">{{ post.title }}</a>
    <p class="post-excerpt">{{ post.content | strip_html | truncatewords: 50 }}
      <a class="post-read-more" href="{{ post.url }}" style="text-shadow: 3px 0px 5px rgba(255,0,255,0.7), -3px 0px 5px rgba(50,50,255,1); font-family: Oxanium, sans-serif;">[ Read more ]</a>
    </p>
  </div>
{% endfor %}
