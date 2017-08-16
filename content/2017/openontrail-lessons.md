Title: Getting started with OpenContrail, Lessons Learned (Part 1)
Date: 2017-08-04
Tags: opencontrail, openstack, SDN, NFV
Category: Networking
Slug: opencontrail-getting-started-lessons-1
Author: Abhijit Gadgil
Summary: OpenContrail provides right set of abstractions for VM and Container networking. However, if one is new to OpenContrail, getting started can be an uphill task. Documenting some of the lessons learned while trying to get started with OpenContrail.

### A bit of a background

A while back while working on Quali Systems [OpenStack Plugin](https://github.com/QualiSystems/OpenStack-Shell), one of the problems we were not trivially able to solve (in fact not able to solve at all using Neutron APIs) was that it was not possible to provide an L2 connectivity to VMs with possibly other Physical networks. Not sure even that exists today. When I looked at OpenContrail back then, it looked like providing all the right abstractions for connectivity, that is both L2/L3 and also recently the Container Network Interface support was added (which I don't know much about as of now!). Exploring what exact features OpenContrail offered was something I wanted to try out.

My initial thinking was, OpenContrail being an Open Source project, this should be fairly straight forward, like many other Open Source projects. Something like -

```bash
git clone
cmake / configure
make
make install
```

Agreed, I am trivializing this quite a lot especially considering the kind of complexity involved in OpenContrail architecture. Minimum I wanted to check was simply the Compute Node component viz. the vrouter, and see how did the data-path looked like. Unfortunately it didn't turn out to be so simple.

On the home page of [OpenContrail](http://www.opencontrail.org), you see two tabs, [Deploy]() and [Quick Start Guide](). It's indeed like - `I am Feeling Lucky`. You try to go to 'Deploy' page and a couple of repositories are mentioned. Looks like - go `git clone` and do the needful from here. Trouble is when you go to [contrail-controller]() or [contrail-vrouter]() repository, there is no such thing as a `Makefile` or `CMakeList.txt` or `configure`. Instead you find an odd looking file called `SConscript`. OpenContrail uses a build system called [scons](http://www.scons.org) and this SconScript is like a recipee for building using `scons`. Unfortnately - no README.md file that gives you a good overview of how to get started in either of the repositories. May be I should have indeed started with the 'Quick Start Guide' document. Ok, let's try that - it starts with a nice 'Overview', explains the 'Architecture' and so on. So now it's time to download and install right? And then you see something like -

Never mind, you still try to 'Register' there. Ideally you'd use something like 'Login with Github' etc. When you click on that - you see -


Now, this starts getting a bit disappointing. While all this while, I didn't notice - that www.opencontrail.org was not an https site. In this day and world? Seriously? So clearly I don't want to use my external data here.

Then I decided, may be this is not how I should go about it. Surely, there must be some repository from where it should be possible to build and install. I look around and finally hit upon a repository that looks like the [build repository](). It atleast has got the `SConstruct` file required by `scons` to build. This being a Python code, I started looking into the file to see what it was doing. Finally, I hit upon a [document]() that looks like  the document that you should refer if you want to build opencontrail code. Unfortunately it doesn't appear that the document is well maintained, so you cannot just follow the instructions there trivially, but it broadly provides a guidance. As discussed in the document, I created a 'sandbox' and started following the instructions as best as I could. This revealed that - OpenContrail uses a tool [repo]() that deals with multiple git repos and is infact the same tool used by Android's build system. Unfortunately, the way scrips and recipees are written is such that, this tries to build `everything` and unfortunately starts with `web-modules`. Somewhere it error out, so I decided to discontinue that path, this will be too much. I really wanted to build ['vrouter'] and that's it.

Ideal would have been something like `devstack`. That you checkout a repository and then simply do a `./stack.sh`. Something like this I was just not able to find - so I decided to create a tool for the same, inspired by `devstack`, I called it [devcontrail](). Interestingly, there's actually a Juniper's repository called [contrail-installer](), that does something pretty similar, sorry exactly like what I wanted to do. In none of the documents that I read, I could find a reference to this repo. At-least something along the lines - ''Clone this repo - and run `./contrail.sh`, but be warned this is tested on Ubuntu 14.04 (trusty) only!'' would have been nice.

So I decided upon a following broad approach -

1. Create a repo that looked like [contrail-build]
2. Add [opencontrail-controller], [opencontrail-vrouter], [opencontrail-sandesh] repositories as git submodules.
3. Keep trying till we are successful.

This looked like a viable approach and I started making some progress. Something worth mentioning here, I wanted to start with building something bare minimum and then build more once I get comfortable with what is getting built and I am able to try at-least some of the things that get built. There's a bit of quirk worth mentioning here, OpenContrail uses a lot of old versions of third party software that is not distributed as a package (either by OpenContrail or officially by Ubuntu/Redhat etc.) Some of the software versions are so old - nearly three years and patches for those versions. It was perhaps easier to have got those changes merged into upstream, so that this quirk could be avoided, unfortunately that doesn't look like the case as of now. One has to leave with 'source downloading' and sometimes 'patching' these third party modules. The patches required for patching some of these `third-party` modules are available from a repository [third-party](). Instead of downloading everything in one go, I decided to do one at a time - something like

```bash
while ! success:
    scons
    if failed:
        look at the failure and update a third-party software and/or install new software.
```

This approach seems to work, however there are a few packages that give trouble - which is worth mentioning here -

1. Cassandra CPP driver - The 'controller' SConscript do not correctly specify the dependency on this (`libcql` inside `controller/lib/libcql`), so I had to create a `SConscript` for that.
2. Kafka CPP libraries - `librdkafka` - Those available from Ubuntu only support C bindings and do not support C++ bindings, those available from `opencontrail:ppa` might support this, but I didn't try that. I instead used the 'third-party' approach with another `SConscript`.
3. IP Fix library - There's a dependency on this rather old `libipfix` for which as well, I just installed by hand, where as document above recommends downloading as a 'third-party'.

Finally with enough trial and error I am able to build both debug and production packages for `controller` and `vrouter`. I have forked these repositories myself, so that changes to SConscripts, I can keep tracking.

However, at this point, I am not continuing further using this approach, instead will start from a 'fork' of the [contrail-installer](), that seems to be the right path and fix that to support at-least major Ubuntu/Fedora and CentOS versions.

Once I am able to complete that - I think we will have what should have been a 'Quick Start Guide'. Let's hope so.
