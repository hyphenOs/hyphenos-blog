Title: So Vector Operations Are Fast, Right?
Date: 2017-08-02
Tags: pandas, numpy
Category: Performancee
Slug: vector-operations-are-fast-right
Author: Abhijit Gadgil
Summary: Recently, I was looking at processing data from Pandas panel. I wanted to find out certain `items` in a Panel based on certain criteria on the `minor axis`. I worked with two flavors and the findings for different data-sets are quite interesting. Something that would definitely qualify as a learning.

### A bit of a background

I am developing a system of processing historical NSE equities data, where I want to look at `interesting` historical observations to be able to look at a subset of `all` stocks that are traded on NSE. While what those 'interesting' observations would be is going to be a function of an investors methodology, but a tool that helps you look at historical data in 'interactive' time frames (typically under 10 seconds) is going to be very handy.

Finally after nearly a few weeks of work, I managed to get a data that was in a form where I could do some experiments with this. The experiments are going to be along two axes - viz. from investment point of view (which the end users might be interested in) and from system point of view - to really answer the question in a reasonable manner - whether it will be really possible to make this available 'as a service' - more about that a bit later. Those curious about the code to download the data and process it can [check it out here](https://github.com/gabhijit/equities-data-utils)

### So coming to concrete problem

I have a Pandas Panel that has got a list of 'stocks' as `items` and we have each `item` which has historical data as a data-frame with date as `index` and 'o,h,l,c' as columns. I wanted to filter based on simple criteria, say last 'close' is higher than previous 'close'.

One approach based on List Comprehensions is -

```python
pan = pd.Panel(scripdata_dict)

# All Items where the following condition is true and
# then use the boolean selectors to select items of our choice.
sels = [pan[x]['close'][-1] > pan[x]['close'][-2] for x in pan]

```

This somehow wasn't looking quite 'elegant' and certainly didn't look in the spirit of Pandas. I was pretty sure, there would be a faster, 'Vector' way of doing this. It took me a bit of time to find that out eventually as I am not quie an expert in Pandas. But eventually after struggling a bit I stumbled upon the following solution, that did what I was looking for -


```python
# Create a transpose of the Panel, now `items` become major axis.
# Select all rows such that the condition is true and then use
# the major axis (which is also an index) of the dataframe of `close` item.

pan2 = pan.transpose(2, 0, 1)
cl = pan2['close']
cl2 = cl[cl.iloc[:, -1] > cl.iloc[:, -2]]
pan11 = pan[cl2.index]

```

This looked good, in theory and in practice too. I had a toy data that I was experimenting with just small data of 20 or so rows that helps you try out things without spending lot of time on loading data. And Voila, the second approach is about *20-40 times faster* than the first one. So the basic intuition is right, it's time to Declare Victory or Is it?.

Now somebody experienced with Pandas would have looked at it and asked 'How big is your data? Are you sure you want to do that? Did you RTFD?'.

So now we take the code and run it against 'real data' - about 3000 or so rows per dataframe in a Panel, and the same code now runs about *3-4 times slower*. What? Seriously? First impression is something else must be wrong. So I start looking at excuses, while the former I was running on my desktop, dedicated CPU and the latter I was running on a VPS, could that be a problem? This was clearly not an Apples-to-Apples comparison. So then I experiment with this 'small data' on the VPS, still the results are about the same. So we can eliminate that as a problem. Clearly size wise, the first one was about 2-3MB and the latter one was about 700MB. Hint, somewhere the Cache effects are coming into play?

The next quest was - how do I find out? My first (and quite wrong at that honestly) effort would be to use the `dtrace` support in Python and use some `perf` counters or tracing tools from the [bcc](https://github.com/iovisor/bcc) to find out. Thankfully, that support is not there in Python 2.7 I am havingon my Ubuntu machine. So what next? Let's run Python's native profilers and find out. Is the intuition even correct? So ran a simple profiling experiment by using the `cProfile` and `pstats`. The code looks like following - fairly straight forward.

For the 'Vector' method -

```python

then0 = time.time()
pr = cProfile.Profile()
pr.enable()

pan2 = pan.transpose(2, 0, 1)
cl = pan2['close']
cl2 = cl[cl.iloc[:, -1] > cl.iloc[:, -2]]
pan11 = pan[cl2.index]

pr.disable()
pr.dump_stats('vector_stats.out')
s = StringIO.StringIO()

# Sort stats by cumulative and print only top 10%
sort_by = 'cumulative'
ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
ps.print_stats(0.1)
ps.print_callers()
now0 = time.time()

```
and for the 'List Comprehension' method -

```python
then0 = time.time()

pr = cProfile.Profile()
pr.enable()

sels = [pan[x]['close'][-1] > pan[x]['close'][-2] for x in pan]

pr.disable()
pr.dump_stats('lc.stats')
s = StringIO.StringIO()

# Sort stats by cumulative and print only top 10%
sort_by = 'cumulative'
ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
ps.print_stats(0.1)

now0 = time.time()

```

Here are the actual Profiling outputs for run on 'small data'.

For the List Comprehension method -

```
0.729673147202
734
         552007 function calls (533140 primitive calls) in 0.704 seconds

   Ordered by: cumulative time
   List reduced from 129 to 13 due to restriction <0.1>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     6288    0.017    0.000    0.472    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:1640(_get_item_cache)
     3144    0.014    0.000    0.361    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:280(__getitem__)
     3144    0.003    0.000    0.334    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:1637(__getitem__)
     1572    0.009    0.000    0.282    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:558(_box_item_values)
     1572    0.012    0.000    0.250    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:261(__init__)
     1572    0.014    0.000    0.229    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:413(_init_ndarray)
     1572    0.009    0.000    0.181    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:4283(create_block_manager_from_blocks)
     3144    0.008    0.000    0.176    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/series.py:598(__getitem__)
     3144    0.012    0.000    0.166    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:1940(__getitem__)
     3144    0.014    0.000    0.166    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/indexes/datetimes.py:1358(get_value)
     1572    0.010    0.000    0.148    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:2779(__init__)
     3144    0.003    0.000    0.144    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:1966(_getitem_column)
     3144    0.029    0.000    0.144    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/indexes/base.py:2454(get_value)


```

For the Vector method -

```
0.0554749965668
734
         7443 function calls (7341 primitive calls) in 0.026 seconds

   Ordered by: cumulative time
   List reduced from 447 to 45 due to restriction <0.1>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    0.012    0.012 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:1202(transpose)
        1    0.001    0.001    0.012    0.012 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:496(transpose)
        1    0.000    0.000    0.008    0.008 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:1940(__getitem__)
        1    0.000    0.000    0.007    0.007 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/indexes/datetimelike.py:249(__contains__)
        1    0.000    0.000    0.007    0.007 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/indexes/datetimes.py:1401(get_loc)
        1    0.000    0.000    0.007    0.007 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/base.py:42(__str__)
        1    0.000    0.000    0.007    0.007 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/base.py:54(__bytes__)
        1    0.000    0.000    0.007    0.007 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/series.py:974(__unicode__)
        1    0.000    0.000    0.007    0.007 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:3256(values)
        1    0.000    0.000    0.007    0.007 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:462(as_matrix)
        1    0.000    0.000    0.007    0.007 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:3438(as_matrix)
        1    0.002    0.002    0.006    0.006 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:3452(_interleave)
        1    0.000    0.000    0.006    0.006 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/series.py:993(to_string)
        1    0.004    0.004    0.004    0.004 {method 'copy' of 'numpy.ndarray' objects}
        2    0.000    0.000    0.004    0.002 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:280(__getitem__)
        1    0.000    0.000    0.004    0.004 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/io/formats/format.py:243(to_string)
      7/5    0.000    0.000    0.003    0.001 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/indexing.py:1317(__getitem__)
        2    0.000    0.000    0.003    0.001 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:160(get_values)
        4    0.003    0.001    0.003    0.001 {method 'astype' of 'numpy.ndarray' objects}

<stripped-a-few-lines>
```

So the data also - justifies the basic intuition, in the case of 'vector' method, there are about 7000 calls compared to about '500000' calls to functions, justifying that _may be_ we are doing more work in the List Comprehensions method.

So why is this so bad? Let's see what it looks like on the real data. Spoiler Alert: A good observer would have noticed that `'copy' method of 'numpy.ndarray' objects` already.

Below is the profiling output on the actual data.

For the List Comprehension method -

```
1.5659070015
689
         550855 function calls (532024 primitive calls) in 1.542 seconds

   Ordered by: cumulative time
   List reduced from 132 to 13 due to restriction <0.1>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     6276    0.038    0.000    1.008    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:1640(_get_item_cache)
     3138    0.032    0.000    0.806    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:280(__getitem__)
     3138    0.008    0.000    0.736    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:1637(__getitem__)
     1569    0.014    0.000    0.635    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:558(_box_item_values)
     1569    0.022    0.000    0.564    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:261(__init__)
     1569    0.025    0.000    0.527    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:413(_init_ndarray)
     1569    0.020    0.000    0.402    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:4283(create_block_manager_from_blocks)
     3138    0.017    0.000    0.397    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/series.py:598(__getitem__)
     3138    0.027    0.000    0.368    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/indexes/datetimes.py:1358(get_value)
     3138    0.024    0.000    0.340    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:1940(__getitem__)
     3138    0.057    0.000    0.323    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/indexes/base.py:2454(get_value)
     3138    0.008    0.000    0.288    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:1966(_getitem_column)
     1569    0.019    0.000    0.284    0.000 /actual/path/to/data/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:2779(__init__)



```
and for the Vector method -

```

7.15247297287
689
         7443 function calls (7341 primitive calls) in 7.138 seconds

   Ordered by: cumulative time
   List reduced from 447 to 45 due to restriction <0.1>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    5.000    5.000 /home/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:1202(transpose)
        1    0.349    0.349    5.000    5.000 /home/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:496(transpose)
        1    0.000    0.000    2.863    2.863 /home/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:3256(values)
        1    0.000    0.000    2.863    2.863 /home/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:462(as_matrix)
        1    0.000    0.000    2.863    2.863 /home/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:3438(as_matrix)
        1    0.644    0.644    2.863    2.863 /home/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:3452(_interleave)
        2    0.000    0.000    2.040    1.020 /home/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:280(__getitem__)
        2    0.000    0.000    1.818    0.909 /home/gabhijit/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:160(get_values)
        4    1.818    0.454    1.818    0.454 {method 'astype' of 'numpy.ndarray' objects}
        1    1.787    1.787    1.787    1.787 {method 'copy' of 'numpy.ndarray' objects}


```

Eureka! The `transpose` function has become extremely expensive for this big data. Note, the number of funtion calls is still about the same, about 7000 vs. 500000, but at-least some of the functions have become exensive and interestingly the total cost was actually growing sub-linearly for the List Comprehension method.

Now, when one looks at this data, it's clearly not that counter intuitive. We are doing a `memcpy` of a huge array in the `transpose` method and that's likely is a cause of real slowdown. While in the former case, there was still `memcpy`, but on a data that could probably fit easily in cache (or at-least was quite cache friendly) compared to this. Didn't they tell in networking don't do `memcpy` in the fast path?

We need to still follow this line of thought and find out more about what's happening under the hood. Some of the things that are worth experimenting include -

1. double the data size and compute the fraction of time spent in `transpose` for every doubling and expect to see a knee somewhere.
2. Does that make sense with the cache size on my computer?
3. Indeed look at the `perf` counters and see some cache statistics.

Will write a follow up on this to actually find out what the findings above are.

Few lessons learnt here -

* Just don't go by what theoretically makes sense. Know precisely what you are trying to do and what scale.
* Simply - going by 'Vector Operations are Fast' so always use them, may not be the wisest choice.
* RTFM - because clearly [documentation on transpose](http://pandas.pydata.org/pandas-docs/version/0.20.3/generated/pandas.Panel.transpose.html) says, for Mixed-dtype data, will always result in a copy.
* Sometimes not having an expert around is not a bad idea, because you develop better understanding by making mistakes.

And a few collateral benefits -

1. Had an actual use-case for studying `cProfile` rather than trying some simple 'hello world!' stuff.
2. Learnt about a beautiful tool [gprof2dot](https://github.com/jrfonseca/gprof2dot), when trying to find out more about the actual call-graphs and find out the culprits. It's worth checking out.

