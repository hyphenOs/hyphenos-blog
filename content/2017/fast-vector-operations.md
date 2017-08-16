Title: So Vector Operations Are Fast, Right?
Date: 2017-08-07
Tags: pandas, numpy
Category: Performance
Slug: vector-operations-are-fast-right
Author: Abhijit Gadgil
Summary: Recently, for one of the projects we are working on, I was looking at processing data from Pandas panel. I wanted to find out certain `items` in a Panel based on certain criteria on the `minor axis`. I worked with two flavors and the findings for different data-sets are quite interesting. Something that would definitely qualify as an interesting learning. We discuss, how profiling can be successfully used to explain certain Performance behavior, that often looks counter-intuitive.

### A bit of a background

One of the applications we are developing is a system of processing historical NSE equities data. What we are developing is a system, where, based on certain criteria relating to historical data of a stock or a set of stocks, one could narrow down the universe of stocks from 'all' stocks in NSE to a few that match certain criteria.
Typically, such criteria will be input by a user as a query to filter stocks. eg. A user might want to query, stocks that are trading above 50 monthly EMA. A design goal of such this system is, one should be able to perform such filtering in 'interactive' time frames, typically not more than few seconds with a budget of not more than 20-30 seconds.

The challenges involved in developing such systems are manifold, if you don't use any public APIs like Quandle or Kite and rely entirely on NSE Bhavcopy data, you have to do a lot of heavy lifting yourself. After doing [considerable heavy lifting](https://github.com/gabhijit/tickpdownload), we started doing some experiments.
The experiments will typically be of the following two kinds -

1. *What* make good filtering criteria - This is what a lot of 'investors' would typically be interested.
2. *How* do you solve the problems that meet the above design goals - viz. run-time queries (so you cannot pre-compute and store data) answered in 'interactive' time frames.

The eventual goal is to develop a 'service' that can be offered to users.

### So coming to concrete problem

We are mainly going to be concerned about the *How* question here. We are going to make use of [pandas](http://pandas.pydata.org/) features to achieve the stuff we are trying to arrive. So at a high level, the idea is - A pandas `Panel` that has got a list of 'stocks' as `items` and we have each `item` which has historical data as a `DataFrame` with date as `index` and 'OHLC' as columns. Since our focus is not on so much on *What* questions to ask, we will take a simple criterion which is stock having a positive close ie. last close is higher than previous close. ie. to put simplistically - `DataFrame.iloc[-1] > DataFraome.iloc[-2]`.

The first solution that I came up with based on List Comprehension -

```python
pan = pd.Panel(scripdata_dict)

# All Items where the following condition is true and
# then use the boolean selectors to select items of our choice.
sels = [pan[x]['close'][-1] > pan[x]['close'][-2] for x in pan]

```

However, after looking at this, it's clearly not a 'fast' 'vector' operation. So likely there's a faster way of doing this using 'vector' operations, after all that's what `numpy` and hence `pandas` is extremely good at. A following approach based on using `transpose` could be useful. I am not sure whether this is 'the fastest way' or there could be an even better way. But we'd continue exploring the following approach -

```python
# Create a transpose of the Panel, now `items` become major axis.
# Select all rows such that the condition is true and then use
# the major axis (which is also an index) of the dataframe of `close` item.

pan2 = pan.transpose(2, 0, 1)
cl = pan2['close']
cl2 = cl[cl.iloc[:, -1] > cl.iloc[:, -2]]
pan11 = pan[cl2.index]

```

This looked clean. To test this, I had a toy data that I was experimenting with just small data of 20 or so rows (I often use such toy data when iterating over an approach, so that you don't end up spending a lot of time in loading the data itself.) Indeed, this approach is about *20-40 times faster*, based on some simple `time.time()` computation. So the basic intuition is right, it's indeed very fast or Is it?.

While, I have a reasonable working knowledge of `pandas`, I am far from an expert and have only some background in `numpy`. So I did not have an idea about how the particular pieces might be implemented (eg. `transpose` here.). Surely, basic test also suggests, it's worth a try. So now we take the code and run it against 'real data' - about 3000 (about 150 times original data) rows per `DataFrame` in a Panel, and the same code now runs about *3-4 times slower* than the first List Comprehension based approach. Oops! Seriously? First impression in such cases is something else must be wrong. So I started looking at explanations, while the former I was running on my desktop, dedicated CPU and the latter I was running on a VPS, could that be a problem? May be I should eliminate that variable first. So I tried the 'toy data' on the VPS, still the results are about the same. So clearly, something else is wrong.

The next question was - how do I find out? My first (and quite wrong at that honestly) effort would be to use the `dtrace` support in Python and use some `perf` counters or tracing tools from the [bcc](https://github.com/iovisor/bcc) to find out. Incidentally, that support is not there in Python 2.7 I am having on my Ubuntu machine. So what next? Let's run Python's native profilers and find out. Is the intuition even correct? So ran a simple profiling experiment by using the `cProfile` and `pstats`. The code looks like following - fairly straight forward.

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

```bash
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

```bash
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

Below is the profiling output on the actual data that is about 3000 rows in a DataFrame.

For the List Comprehension method -

```bash
1.5659070015
689
         550855 function calls (532024 primitive calls) in 1.542 seconds

   Ordered by: cumulative time
   List reduced from 132 to 13 due to restriction <0.1>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     6276    0.038    0.000    1.008    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:1640(_get_item_cache)
     3138    0.032    0.000    0.806    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:280(__getitem__)
     3138    0.008    0.000    0.736    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:1637(__getitem__)
     1569    0.014    0.000    0.635    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:558(_box_item_values)
     1569    0.022    0.000    0.564    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:261(__init__)
     1569    0.025    0.000    0.527    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:413(_init_ndarray)
     1569    0.020    0.000    0.402    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:4283(create_block_manager_from_blocks)
     3138    0.017    0.000    0.397    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/series.py:598(__getitem__)
     3138    0.027    0.000    0.368    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/indexes/datetimes.py:1358(get_value)
     3138    0.024    0.000    0.340    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:1940(__getitem__)
     3138    0.057    0.000    0.323    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/indexes/base.py:2454(get_value)
     3138    0.008    0.000    0.288    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/frame.py:1966(_getitem_column)
     1569    0.019    0.000    0.284    0.000 /actual/path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:2779(__init__)



```
and for the Vector method -

```bash

7.15247297287
689
         7443 function calls (7341 primitive calls) in 7.138 seconds

   Ordered by: cumulative time
   List reduced from 447 to 45 due to restriction <0.1>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    5.000    5.000 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:1202(transpose)
        1    0.349    0.349    5.000    5.000 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:496(transpose)
        1    0.000    0.000    2.863    2.863 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/generic.py:3256(values)
        1    0.000    0.000    2.863    2.863 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:462(as_matrix)
        1    0.000    0.000    2.863    2.863 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:3438(as_matrix)
        1    0.644    0.644    2.863    2.863 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:3452(_interleave)
        2    0.000    0.000    2.040    1.020 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/panel.py:280(__getitem__)
        2    0.000    0.000    1.818    0.909 /path/to/data/equities-data-utils/venv/local/lib/python2.7/site-packages/pandas/core/internals.py:160(get_values)
        4    1.818    0.454    1.818    0.454 {method 'astype' of 'numpy.ndarray' objects}
        1    1.787    1.787    1.787    1.787 {method 'copy' of 'numpy.ndarray' objects}

```

Eureka! The `transpose` function has become extremely expensive for this big data. Note, the number of function calls is still about the same, about 7000 vs. 500000, but at-least some of the functions have become expensive and interestingly the total cost was actually growing sub-linearly for the List Comprehension method.

Now, when one looks at this data, it's clearly not that counter intuitive. We are doing a `memcpy` of a huge array in the `transpose` method and that's likely is a cause of real slowdown. While in the former case, there was still `memcpy`, but on a data that could probably fit easily in cache (or at-least was quite cache friendly) compared to this. A lesson from 'networking data-path 101' don't do `memcpy` in the fast path.

We need to still follow this line of thought and find out more about what's happening under the hood. Some of the things that are worth experimenting include -

1. double the data size and compute the fraction of time spent in `transpose` for every doubling and expect to see a knee somewhere.
2. Does that make sense with the cache size on my computer?
3. Indeed look at the `perf` counters and see cache statistics.

Will write a follow up on this to actually find out what the findings above are.

Few lessons learned here -

* Just don't go by what theoretically makes sense. Know precisely what you are trying to do and what scale.
* RTFM - because clearly [documentation on transpose](http://pandas.pydata.org/pandas-docs/version/0.20.3/generated/pandas.Panel.transpose.html) says, for Mixed-dtype data, will always result in a copy.
* Sometimes not having an expert around is not a bad idea, because you develop better understanding by making mistakes.

And a few collateral benefits -

1. Had an actual use-case for studying `cProfile` rather than trying some simple 'hello world!' stuff.
2. Learned about a beautiful tool [gprof2dot](https://github.com/jrfonseca/gprof2dot), when trying to find out more about the actual call-graphs and find out the culprits. It's worth checking out.

