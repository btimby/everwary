[![Travis CI Status](https://travis-ci.org/btimby/everwary.png)](https://travis-ci.org/btimby/everwary)

[![Code Coverage](https://coveralls.io/repos/btimby/everwary/badge.png?branch=master)](https://coveralls.io/r/btimby/everwary)

EverWary
========

Everwary is your ever watchful eye in the cloud. It is an IP camera management
application written in Django. This application provides the following functionality.

 * FTP Server - Some IP cameras use FTP to send a still image when motion is
   detected. The EverWary FTP server will receive these stills and trigger
   video recording.
 * SMTP Server - Some IP cameras use SMTP to email a still image when motion
   is detected. The EverWary SMTP server will receive these stills and
   trigger video recording.
 * Alerts - In addition to recording video when motion is detected, an alert
   can be sent for such events.
 * Device Monitoring - A camera that is unreachable is a possible security
   breach. Alerts are sent when cameras become unavailable, and again when they
   recover.
 * Cloud Video Storage - Videos are stored in your favorite cloud provider.

Consumption
===========

This project consists of an Open Source code base as well as a number of
means to utilize the code base.

First of all, you can install the code onto your own server and run your own
installation. You can choose to store videos locally or in the cloud.

Secondly, an EC2 image is provided to run in the cloud. This image is
preconfigured to store videos to S3.

Lastly, everwary.com provides access to a turnkey service. The service is
completely free and integrates with your favorite cloud provider. The code
backing the service is the same code located in this repository.

Installation
============

If you decide to install the software, you can do so using the following
instructions.

1. You need Python and Gearmand, install them using the usual means. On
   Fedora/RedHat systems this means.


    $ sudo yum install gearmand python

2. Clone this repository.


    $ git clone https://github.com/btimby/everwary.git

3. Use the Makefile to create the virtualenv.


    $ cd everwary
    $ make env

4. You can start the application by running the following commands.


    $ python manage.py syncdb
    $ source env/bin/activate
    $ circusd -c bin/circus.ini

This will spawn several instances of the worker as well as the web application.
At this point, you will have a fully-functional installation minus cron jobs.
You can easily configure the cron job by adding the following to your crontab.


    $ crontab -e

    * * * * *    /path/to/everwary/env/bin/python /path/to/everwary/everwary/manage.py cron

Configuration
=============

Being a Django application, there are many configuration switches you can
change. This application supports a settings_local.py file in which you can
override any of the defaults present in settings.py. See
`everwary/settings_local.py.template` for some examples.

Cameras
=======

Before you can log in and start adding cameras, they must be accessible to the
EverWary server. This means the usual filtering/NAT port forwarding rules to
allow at least the server to hit the HTTP(S) ports on the camera. Once you add
a camera to EverWary, you can auto-configure it, which will set the camera up
using the optimal configuration for the given model.

Development
===========

If you plan to contribute to the effort, there are a few things to know. First
of all, the Django unit test framework is utilized for unit tests. Secondly,
Makefiles are used to provide shortcuts for many of the common operations,
review the Makefiles to get an idea of what commands you will need to use.

Travis CI is used to execute the unit tests.
Coveralls.io is used to perform code coverage reporting for unit tests.

Stack
=====

This application uses the following architecture.

Asynchronous jobs such as video capture are handled using Gearman and the
Excellent python-gearman library. Video capture itself is done using ffmpeg.
A simple plugin system allows support for various cameras to be added easily.
Django REST Framework was used to build a full REST API for all data. The web
UI was built atop the API using Bootstrap, backbone.js, and jQuery.
Circus/Chaussette/Meinheld/Apache are used to run the Python WSGI application.
Scheduled tasks such as camera pings are handled using cron, which injects
tasks into Gearman.

Mobile
======

The Web UI was carefully tuned to work with mobile devices, specifically mine:
Samsung Galaxy III. I also plan to implement a simple mobile app that can be
used to toggle zones (groups of cameras) for when you visit a site. This mobile
app will be written using phonegap and utilize the REST API.

Genesis
=======

So, there are a lot of IP camera monitoring solutions, but none met my
requirements. I needed to monitor emtpy rental houses for burglary, which meant
I needed a system that could be moved from house to house as they become
(un)occupied. I wanted to use a cellular connection for this purpose which
means bandwidth is restricted. Many services do motion detection on the
server-side which requires 24x7 streaming (dropcam). Other solutions did not
monitor and alert when cameras became unreachable. I also wanted a solution
that could run in a data center, so no desktop software (Blue Iris). Also,
since all of my systems run Linux any Windows only solution is not acceptable
(ispy-connect). Being a huge Open Source proponent meant that all commercial
solutions were disregarded.