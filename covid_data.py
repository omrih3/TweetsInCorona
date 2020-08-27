import os
import matplotlib
from matplotlib import pyplot
from matplotlib import dates
from datetime import datetime

import pandas
import twint

from numpy import average, max, zeros, ones
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
date_format = '%Y-%m-%d'

class CovidData:
    def __init__(self):
        self.all_data = pandas.read_csv('data/full_grouped.csv')

    def get_table_by_country(self, country):
        return self.all_data[(self.all_data['Country/Region'] == country)]


class CovidTwits:
    account_dict ={'US': ["@BarackObama", "@katyperry", "@taylorswift13", "@ladygaga", "@realDonaldTrump", "@TheEllenShow",
                          "@ArianaGrande", "@KimKardashian", "@jtimberlake", "@selenagomez", "@britneyspears", "@ddlovato",
                          "@jimmyfallon", "@BillGates", "@KingJames", "@JLo", "@MileyCyrus", "@Oprah","@BrunoMars",
                          "@wizkhalifa"],
                    'United Kingdom':["@GarethBale11", "@Harry_Styles", "@Louis_Tomlinson", "@LiamPayne", "@onedirection", "@EmmaWatson",
                        "@zaynmalik", "@edsheeran", "@Adele", "@coldplay",'@BorisJohnson', '@NicolaSturgeon', '@piersmorgan',
                                      '@carolecadwalla', '@Keir_Starmer'],
                    'Canada':  ["@Drake", "@elonmusk", "@ShawnMendes", "@AvrilLavigne", "@theweeknd",
                                "@carlyraejepsen", "@Sethrogen", "@ninadobrev", "@laurDIY", "@JustinTrudeau", '@TypicalGamer', '@richbrian',
                               '@WilliamShatner','@BizNasty2point0','@RealKidPoker','@Cmdr_Hadfield','@GailVazOxlade'],
                    'Australia':  ["@RealHughJackman", "@5SOS", "@Luke5SOS", "@Michael5SOS", "@troyesivan",
                      "@Calum5SOS", "@CodySimpson", "@chrishemsworth", "@Ashton5SOS", "@MirandaKerr",
                      "@ScottMorrisonMP", '@russellcrowe','@Tim_Cahill','@QuadeCooper','@larryemdur','@scottdools','@sarahinthesen8',
                                   '@macleanbrendan','@PMOnAir','@jothornely']
                   }
    KEYWORDS = ["coronavirus", "covid19", "covid-19", "Covid-19",
            "Covid19","COVID-19", "Coronavirus", "COVID19", "COVID_19", "COVID2019", "COVID", "covid", "Corona"]

    def __init__(self):
        self.data = {}
        self.by_date = {}
        self.date_mood = {}

    def load(self, country, non_covid):
        if non_covid:
            csv_name = f'{country.replace(" ", "_")}_twits_non_covids.csv'
        else:
            csv_name = f'{country.replace(" ","_")}_twits.csv'
        if not os.path.isfile(csv_name):
            self.create_all_twits_file(country, csv_name, non_covid)
        self.data[country] = pandas.read_csv(csv_name)
        for row in self.data[country].itertuples():
            date = row.date
            if date in self.by_date:
                self.by_date[date].append(row.tweet)
            else:
                self.by_date[date] = [row.tweet]
        self.by_date = {date: list(set(tweet_list)) for date, tweet_list in self.by_date.items()}

    def get_date_num_of_tweets(self):
        return {date:len(tweet_list) for date, tweet_list in self.by_date.items()}

    def run_sentiment_analysis(self):
        analayzer = SentimentIntensityAnalyzer()
        date_mood = {date: average([analayzer.polarity_scores(tweet)['compound'] for tweet in tweet_list]) for date, tweet_list
                     in self.by_date.items()}
        self.date_mood = date_mood
        return date_mood

    def get_sentimal_date_range(self, from_date, to_date):
        self.run_sentiment_analysis()
        from_date = datetime.strptime(from_date, date_format)
        to_date = datetime.strptime(to_date, date_format)
        ordered_data = sorted(self.date_mood.items(), key=lambda x: datetime.strptime(x[0], date_format))
        avg = 0
        counter = 0
        for date, sentimal in ordered_data:
            this_date = datetime.strptime(date, date_format)
            if from_date < this_date < to_date:
                counter += 1
                avg += sentimal
            elif this_date > to_date:
                break
        avg = avg / counter
        return avg

    def create_all_twits_file(self, country, file_name, non_covid):
        config = twint.Config()
        for user in self.account_dict[country]:
            print(f'Searching for user {user}')
            config.Username = user
            config.Limit = 2000
            config.Lang = "en"
            config.Store_csv = True
            config.Output = file_name
            if non_covid:
                config.Since = '2020-01-01 00:00:00'
                twint.run.Search(config)
            else:
                for key in self.KEYWORDS:
                    print("[INFO] Searching for keyword: " + key)
                    config.Search = key
                    twint.run.Search(config)

class CountryGraph:
    def __init__(self, country, non_covid):
        self.covid_data = CovidData().get_table_by_country(country)
        self.tweet_tool = CovidTwits()
        self.tweet_tool.load(country, non_covid)
        self._country = country

    def plot_sentimal(self, covid_info):
        allowed_dates = self.covid_data['Date'].unique()
        sentimal_data = self.tweet_tool.run_sentiment_analysis()
        ordered_data = sorted(sentimal_data.items(), key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))[1:]
        ordered_data = [tup for tup in ordered_data if tup[0] in allowed_dates]
        date_list = [tup[0] for tup in ordered_data]
        sentimal_list = [tup[1] for tup in ordered_data]
        converted_dates = list(map(datetime.strptime, date_list, len(date_list) * ['%Y-%m-%d']))
        x_axis = converted_dates
        formatter = dates.DateFormatter('%Y-%m-%d')

        new_confirmed_list = [self.covid_data.loc[self.covid_data['Date'] == date, covid_info].iloc[0]
                              for date in date_list if date in allowed_dates]
        max_new = max(new_confirmed_list)
        new_confirmed_list = [(2*(num/max_new))-1 for num in new_confirmed_list]

        average_factor = 24
        chunk_length = int(len(sentimal_list) / average_factor)
        average_sentimal_list = [0]*len(sentimal_list)
        for i in range(average_factor):
            avg = average(sentimal_list[i*chunk_length:(i+1)*chunk_length])
            average_sentimal_list[i*chunk_length:(i+1)*chunk_length] = [avg]*chunk_length
        # pyplot.plot(x_axis, sentimal_list, '-', label='Sentiment analysis of Tweets')
        pyplot.plot(x_axis, average_sentimal_list, '-', label=f'Average (per week) Sentiment analysis of Tweets')
        pyplot.plot(x_axis, new_confirmed_list, '-', label=f'Covid-19 {covid_info} normalized to [-1,1]')
        pyplot.title(f'Covid-19 And Positivity Of Tweets In {self._country}')
        ax = pyplot.gcf().axes[0]
        ax.xaxis.set_major_formatter(formatter)
        pyplot.gcf().autofmt_xdate(rotation=25)
        pyplot.legend()
        pyplot.show()

    def plot_num_of_tweets(self, covid_info):
        allowed_dates = self.covid_data['Date'].unique()
        num_of_tweets_data = self.tweet_tool.get_date_num_of_tweets()
        ordered_data = sorted(num_of_tweets_data.items(), key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))[1:]
        ordered_data = [tup for tup in ordered_data if tup[0] in allowed_dates]
        date_list = [tup[0] for tup in ordered_data]
        num_of_tweets_list = [tup[1] for tup in ordered_data]
        converted_dates = list(map(datetime.strptime, date_list, len(date_list) * ['%Y-%m-%d']))
        x_axis = converted_dates
        formatter = dates.DateFormatter('%Y-%m-%d')

        new_confirmed_list = [self.covid_data.loc[self.covid_data['Date'] == date, covid_info].iloc[0]
                              for date in date_list if date in allowed_dates]
        max_new = max(new_confirmed_list)
        new_confirmed_list = [(max(num_of_tweets_list)*(num/max_new)) for num in new_confirmed_list]


        y_axis = num_of_tweets_list
        pyplot.plot(x_axis, y_axis, '-', label='num of Tweets')
        pyplot.plot(x_axis, new_confirmed_list, '-', label=f'{covid_info} normalized ')
        pyplot.title(f'Covid in {self._country}')
        ax = pyplot.gcf().axes[0]
        ax.xaxis.set_major_formatter(formatter)
        pyplot.gcf().autofmt_xdate(rotation=25)
        pyplot.legend()
        pyplot.show()

    def get_date_range_sentimal(self, from_date, to_date):
        return self.tweet_tool.get_sentimal_date_range(from_date, to_date)


if __name__ == '__main__':
    # data = CovidData()
    # for row in data.get_table_by_country('Israel').itertuples():
    #     print(f'{row.Date} - {row._9}')
    us_graph = CountryGraph('US', non_covid=True)
    us_graph.plot_sentimal('New cases')

    # # date range compare countries
    # countries_to_compare = ['US', 'United Kingdom', 'Australia', 'Canada']
    # from_date, to_date = '2020-3-15', '2020-4-1'
    # fig = pyplot.figure(figsize=(10, 5))
    # sentimal_avg = [CountryGraph(country, non_covid=True).get_date_range_sentimal(from_date, to_date) for country in countries_to_compare]
    # pyplot.bar(countries_to_compare, sentimal_avg)
    # pyplot.title(f'Average Sentiment of Tweets between {from_date} to {to_date}')
    # pyplot.show()
