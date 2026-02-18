---
layout: sidebar
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
    <a href="#{{ tag | first | slugify }}" style="font-size: {{ tag | last | size  |  times: 4 | plus: 80  }}%"> &rarr;{{ tag[0] | replace:'-', ' ' }} </a> &nbsp;&nbsp;&nbsp;
</span>
{% endfor %}
</div>

<br>
<hr>
<br>

{% for tag in site.tags %}
  <h3 id="{{ tag[0] | slugify }}" style="text-shadow: 3px 0px 5px rgba(255,0,255,0.7), -3px 0px 5px rgba(50,50,255,1);">{{ tag[0] }}</h3>
  <ul style="background-color:rgba(49,27,160,.4);">
    {% for post in tag[1] %}
      <li><a href="{{ post.url }}">{{ post.title }}</a></li>
    {% endfor %}
  </ul>
{% endfor %}
