---
layout: page
title: Tags
permalink: /tags/
---

<style type='text/css'>
    ul {
      list-style-type: circle;
      list-style-position: inside;
      padding: 0;
    }
    li {
        padding: 0 1rem;
	}
    li:hover {
          list-style-type: disc;
          padding: 0 .5rem;
    }
</style>

<div style="div { display: block; height:72px; margin:-72px 0 0; }">
{% for tag in site.tags %}
 <span>
    <a href="#{{ tag | first | slugify }}"> &rarr;{{ tag[0] | replace:'-', ' ' }} </a> &nbsp;&nbsp;&nbsp;
</span>
{% endfor %}
</div>

<br>
<hr>
<br>

{% for tag in site.tags %}
  <h3 id="{{ tag[0] | slugify }}">{{ tag[0] }}</h3>
  <ul>
    {% for post in tag[1] %}
      <li><a href="{{ post.url }}">{{ post.title }}</a></li>
    {% endfor %}
  </ul>
{% endfor %}
