---
title: Hello world mark 3 and why and how I migrated from wordpress to Jekyll.
date: 2019-03-02T22:00:43+00:00
author: paolo
layout: post
permalink: /2019/03/02/hello-word-mark-3/
categories:
  - en-US
tags:
  - random
  - ruby
---

# Why and how I migrated from wordpress to Jekyll.


First, I've tried to avoid that for years. Wordpress looked like something good, easy and I've been using it since 2011. But everything has a time to go. For the replacement, I found Jekyll! Jekyll is simple, fast and elegant, allowing me to store the blog on github pages and commit new posts or just ssh into my instance and add things. Markdown files seems like the way to go.

## Install 

To install jekyll is very simple. Assuming that you have `ruby`, just make a:
```
gem install jekyll
```
To create a new blog:
```
jekyll new randombox
```
and to test, just go inside and:
```
bundle exec jekyll serve
```
Now, I need to get all the old info from my wordpress blog. For that I used the extension [jekyll-exporter](https://wordpress.org/plugins/jekyll-exporter/), which creates a zip file of all of my posts, pages, and custom post types, as well as the contents of the `wp-content/uploads` directory with all of uploaded images. It was almost perfect but there was some sharp edges like hardcoded image url, that I've solved with a simple bash:

```
grep -rli "http://paolo.zone/blog/wp-content" . | xargs -I@ sed -i '' 's/http:\/\/paolo\.zone\/blog\/wp-content/\/wp-content/g' @
```

my blog was on /blog so I had to set, on config, `baseurl: /blog` and routing was ok, but not wp-based data, which I had to:

sed -i 's/\/wp-content/\{\{ site.baseurl \}\}/g' _posts/*

and that's it.

{% raw %}
For *tags*, I created a `tags.md` :
```
$ cat tags.md
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
      <li><a href="/blog/{{ post.url }}">{{ post.title }}</a></li>
    {% endfor %}
  </ul>
{% endfor %}
```

the only remaining thing was tune my index.md to give a little bit more information than just the post title.
```
---
layout: page
---
<main class="container">
  <div class="row">
    <div class="col-2">
      <br/>
      {% for post in site.posts %}
        <div class="post-meta" style="color:#000;">{{ post.date | date: '%B %d, %Y' }}  <div style="color:#c0c0c0;font-size: 11px;">{{ post.tags | join:", " }}</div> </div>
        <a class="post-link" href="{{ site.baseurl }}/{{ post.url }}">{{ post.title }}</a>
        <p class="post-meta">{{ post.content | strip_html | truncatewords: 50 }}
          <a class="post-link" href="{{ site.baseurl }}/{{ post.url }}" style="font-size: 14px;text-align:right;">[ Read more ]</a>
        </p>
      <br/>
      {% endfor %}
    </div>
  </div>
</main>
```
{% endraw %}

Also, I `ln -s` the self-generated *_site/* directory to my /var/www/html/blog. From this point on, whenever I need to make any modification, I just need to re-run `bundler exec jekyll build` and nothing else.

and that's all. 
