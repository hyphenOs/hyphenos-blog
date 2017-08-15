Title: Hello Static Site Generator
Date: 2017-08-03
Tags: pelican
Slug: hyphenos-hello-world
Author: Abhijit Gadgil
Summary: Started hyphenOs blog on github pages, that is powered by Pelican. This articlue describes the setup.

## Pelican Powered blog for hyphenOs

Traditionally, if one wanted to host a blog, one would typically be doing something like [Wordpress](https://wordpress.com/) or [Blogger](https://wordpress.com/). However writing blogs there is extremely inconvenient to say the list. Plus you want to version control your blog and so on. The solution to these problems is typically - the Static File Generators like [Jekyll](http://jekyllrb.com/) or [Pelican](https://blog.getpelican.com/). Well, there are a [number of those](https://www.staticgen.com/) if one thinks that the above choices are rather limited :-).

Advantage of `Jekyll` is, it is natively supported by Github Pages thus making it easier to use that if you want to quickly get started with your own GitHub page `foo.github.io`. The interested people can read the [documentation](https://guides.github.com/features/pages/) and get started.

For `hyphenOs` blog, I wanted to use pelican FWIW. A small issue with this is - since it's not natively supported by Github Pages, it's a bit of an issue to keep track of your posts and also making sure your generated output is pushed to a respective <foo>.github.io repository. So how does one go about it? We make interesting use of `git submodule` to achieve this. Note: what is described can as well work with gh-pages repo (or I hope so.).

This approach is explained in a couple of [blog](http://railslide.io/pelican-github-pages.html) [posts](http://martinbrochhaus.com/pelican2.html) and I am pretty sure there are many more who go into a lot of details. What I am going to describe here is simply how to use `output` and `theme` directory as `git submodule`, so that everythng is version controlled.

We basically need three repositories here -

1. Content repository - Typically you could create a directory with name blog here. For instance I use directory [hyphenos-blog](https://github.com/hyphenOs/hyphenos-blog) to keep all the content.
2. Output repository - This is where your 'site' will be generated. So for this particular blog I use [hyphenOs.github.io](https://github.com/hyphenOs/hyphenOs.github.io).
3. Theme repository - This is where you will use from a lot of [publicly available](http://www.pelicanthemes.com/) themes. One can use whichever, but the best choice is to use Get Pelican's own [Theme Repository](https://github.com/getpelican/pelican-themes). A very interesting thing about this repository is - a number of themes themselves are available as `git submodules`, making it easier to experiment with different themes.

What we are essentially going to do is Output repository and Theme repository are going to be `git submodules` of our Content repository. So the work-flow becomes.

* Init Content Repository (see below for more details).
* Add Output repository as `git submodule`. `git submodule add https://path-to-your.git output`
* Add Theme repository as `git submodule`. `git submodule add https://github.com/getpelican/pelican-themes theme`
* Add Content to your repository Using Markdown or RST or any Pelican supported Syntax.
* Run `make`. (Wow!)

## Initializing the Content

Normally, in any Python project, I make use of `virtualenv`. This helps in more than one ways especially if you are working with many Python based projects simultaneously. Since Pelican is written in Python and we are going to make use of it to generate our site, as usual, I start with a `virtualenv`.

1. `$virtualenv venv` and then
2. `venv/bin/pip install pelican`. Since I am going to use Markdown, I also
3. `venv/bin/pip install markdown`. After this
4. Run `venv/bin/pelican-generator` utility to set blog wide defaults (be sure to create a `Makefile`, it's very convenient.).
5. Next we should edit the `Makefile` to point to correct Python and Pelican executables. Change `PY?=python` to `PY?=venv/bin/python` and similarly for `PELICAN?=pelican` to `PELICAN?=venv/bin/pelican` in the Makefile.
6. Start writing stuff.

## Changing Theme

In order to use the non-standard theme, one downloaded from the Themes repository above, one can simply add a variable like `THEME = themes/Flex` to `pelicanconf.py` file. To be able to use this - you have to do `git submodule update --remote --recursive` inside the `themes/Flex` directory, since that itself is a `git submodule`. Since I am not interested in all the themes now, I am not doing a `git submodule init` here. Instead I am just taking whatever I am interested in.
