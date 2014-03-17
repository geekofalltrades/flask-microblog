[![Build Status](https://travis-ci.org/geekofalltrades/flask-microblog.png?branch=master)](https://travis-ci.org/geekofalltrades/flask-microblog)

Flask Microblog
------

This project implements a rudimentary blogging wsgi app using flask,
and persists its data with a PostgreSQL database. So far, the functionality
implemented allows users to write a post by giving it a title and a body.
A datestamp is then applied to the post automatically at its time of creation.
Users may also retrieve a list of posts in reverse order added (as is
usually the default format on blog pages) and can retrieve single posts
by their id number (a PostgreSQL serial primary key).

I looked to [Justin Lee's](https://github.com/risingmoon) work on our poker room collaboration for tips
on how to manage deployment and serve static files through nginx.