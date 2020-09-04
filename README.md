# TweetsInCorona
In this projects we measure the influence of the corona virus on the positivity of tweets.

The main.py file contain the API for all the analysis.
The class CountryGraph is the most intersting one. It can show statistic for countries (US, UK, Canada, Australia).
An example for the API:
> from main.py import CountryGraph
> us_graph = CountryGraph('US', non_covid=True)
> us_graph.plot_plot_sentimal("new cases") has 
after executing this code it will create an csv file with the tweets (if not already created) and plot the graph.

The API has many more function and statistics.

This Project has an website with the result of the research: https://hadarh65.wixsite.com/mysite
