# r/algobetting Full Archive

**Scraped**: 2026-04-12
**Total unique posts collected**: 327
**Posts included**: 58 unique posts across 21 categories
**Comments fetched**: 329

---

## Table of Contents

- [Data Sources, APIs & Scraping](#data-sources-apis-scraping) (25 posts)
- [Results, ROI & Profitability](#results-roi-profitability) (18 posts)
- [Statistical Models & Methods](#statistical-models-methods) (16 posts)
- [Backtesting & Validation](#backtesting-validation) (16 posts)
- [NBA / Basketball](#nba-basketball) (13 posts)
- [Expected Value & Edge Detection](#expected-value-edge-detection) (11 posts)
- [Feature Engineering](#feature-engineering) (12 posts)
- [NFL / Football](#nfl-football) (10 posts)
- [Soccer / Football](#soccer-football) (8 posts)
- [Props & Totals](#props-totals) (9 posts)
- [Account Limits & Sportsbook Issues](#account-limits-sportsbook-issues) (4 posts)
- [Betting Exchanges](#betting-exchanges) (5 posts)
- [MLB / Baseball](#mlb-baseball) (5 posts)
- [Closing Line Value & Market Efficiency](#closing-line-value-market-efficiency) (8 posts)
- [Bankroll Management & Kelly Criterion](#bankroll-management-kelly-criterion) (6 posts)
- [Machine Learning Approaches](#machine-learning-approaches) (8 posts)
- [Tennis](#tennis) (3 posts)
- [NHL / Hockey](#nhl-hockey) (2 posts)
- [Getting Started & Beginner Advice](#getting-started-beginner-advice) (3 posts)
- [Arbitrage & Sure Bets](#arbitrage-sure-bets) (4 posts)
- [General Discussion](#general-discussion) (4 posts)

---

## Key Insights Summary

### What Actually Works (consensus from profitable bettors)

- **Closing Line Value (CLV)** is the single most reliable proxy for whether you have a real edge
- **Pinnacle closing lines** are the benchmark -- consistently beating Pinnacle close = real edge
- **Simple models often outperform complex ones** -- Poisson, ELO, logistic regression before jumping to ML
- **Soft books** (DraftKings, FanDuel, BetMGM) have the most exploitable lines
- **Account limits are inevitable** if you win -- diversify across books and use P2P exchanges
- **1-5% ROI is realistic** for a good model; sustained 10%+ ROI claims are almost always false
- **Kelly criterion** (fractional, typically 0.25x-0.5x) is standard bankroll management
- **Speed matters** -- getting on lines early before sharp money moves them is critical
- **Sample size matters** -- need 1000+ bets minimum to evaluate a model with any confidence
- **The-Odds-API and Pinnacle** are the most recommended data sources

### What Does NOT Work

- Buying picks/tipster services (almost universally negative ROI after fees)
- Pure ML without domain knowledge (garbage in = garbage out)
- Ignoring closing line value (profitable short-term but losing long-term = bad model)
- Betting parlays for edge (correlated parlays in specific spots are the exception)
- Chasing ROI% instead of EV (a 20% ROI on 50 bets means nothing)

---

## Data Sources, APIs & Scraping

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [Tennis Analysis #2: Upset Victories](https://reddit.com/r/algobetting/comments/11v0289/tennis_analysis_2_upset_victories/)
**Author**: u/quant_boy123 | **Score**: 12 | **Comments**: 1 | **Date**: 2023-03-18

Hello everyone,

It has been a while since I started what was supposed to be a series focused on tennis analysis from a sports betting perspective. In my first [post](https://www.reddit.com/r/algobetting/comments/ujmpv7/tennis_analysis/), I gave some insights into my motivation and an overview of my data. I also discussed two topics, Implied vs. Realized Probability in tennis betting and O/U Game Lines (theory vs. reality). Moreover, I conducted some backtests based on very simple strategies.

&amp;#x200B;

* Background

My goal for the future is to post more frequently and thereby give you all some trading ideas and valuable insights into tennis analytics. I will typically start with some theory, derived statistics and eventually show some real world betting strategies based on the findings. Whether they would be profitable or not is irrelevant, as both can provide important insights. A bad bet not taken is probably equally valuable as a good bet.

&amp;#x200B;

* Data

For this article, I am only looking at men’s results in official matches for which I have a minimum threshold of data required for the research. My dataset has been growing rapidly recently, since all tournaments have started to resume from the COVID break. Overall, 2022 saw a similar amount of matches as 2016-2019 did (roughly 30000 with clean data) and 2023 is on track to match that. It is important to note that both the quality and quantity of data increased steadily, with more than 60% of the high quality data coming from years &gt;2015.

&amp;#x200B;

* Surprising Outcomes

Today I want to look at upset victories/wins. My definition of an upset is based on bookmaker odds, not on ranking or any other statistics. Bookmaker odds reflect the best guess for the outcome of a match in an efficient market, since they not only take into account the ranking of the two players or their form, but also factors such as the surface, head to head outcomes between the two players and more. Therefore, an upset win can be defined as a win of a player with odds greater than a threshold, let’s say 3 (= Implied Probability roughly 30%, adjusted for vig). 

Firstly, I filter the data to only include players with at least 20 completed matches. Secondly, I exclude players with less than 5 upset wins. Then I start with looking at upset wins with a threshold odd of 3, so every win of a player with odds &gt;3 qualifies as upset win. Since surprises tend to scale with matches played, I rank the outcome by the percentage of upset wins to total matches the player entered as an underdog with odds &gt;3.

Most players making the top 50 of that statistics are ‘newer’ players. This has to do with the fact that most of the high quality data is from recent years, as explained in the Data section. Thus, upset wins from players like Novak Djokovic or Roger Federer are very unlikely, since the data is mainly from a time when they were entering almost every match as a favorite and if they were an underdog, it was typically not with odds &gt;3. 

It is straightforward to see that upset victories typically come at the early stages of the career of a tennis player. That is, when the bookmakers do not have enough information about a players skill. Once they have made some surprising wins, bookmakers lower the odds of the player in subsequent matches to reflect the updated information about their skill level more accurately. Their next wins may therefore not qualify as upset wins anymore, since the odds can be significantly lower than the threshold. This becomes obvious when looking at the odds history of a player like Carlos Alcaraz.

[Graph 1: Carlos Alcaraz ranking vs rolling median odds with a window length of 25 matches.](https://preview.redd.it/k4ugps6iyjoa1.png?width=432&amp;format=png&amp;auto=webp&amp;v=enabled&amp;s=ad92a53e46c91a5f801f8693b075dde24a266b77)

In this graph, the median odds with a rolling window of 25 matches are used. This has the advantage that the curve is smooth and a trend can be easily spotted. Median odds are used instead of average, since the average can plateau on a high level due to one match against a top opponent, for instance Nadal in the French Opens, with very high odds.

In his early days in 2019, when he was first competing in challengers and mainly futures, he often was the underdog. After quick initial success, however, he mainly entered futures tournament matches as the favorite. The same happened in challenger matches in 2020, when he dominated almost every tournament he entered. In 2021, he shifted focus to main tour events, where he often was the underdog. This is where his median odds increase again. In 2022 he had some great victories in the main tour, thus his odds decreased and are now among the lowest of all players, making him the favorite in almost any matchup.

In the following graph, we follow a simple strategy: bet 1 unit on Alcaraz whenever the odds are &gt;3. Obviously, this is with a good portion of hindsight and not a f

[... truncated, see original post ...]

**Top Comments:**

> **u/zahaha** (1 pts): As someone who just got into modeling Woman's Tennis, these are amazing. Please keep it up!

You ever look at live betting trends? Im sure its very hard to get the historical live lines but im curious if there are any situations when "if the pre match odds are &gt;-200 and the live line gets to +300, always take it", or stuff like that.
>

---

### [Common Questions](https://reddit.com/r/algobetting/comments/119hp1j/common_questions/)
**Author**: u/zahaha | **Score**: 10 | **Comments**: 4 | **Date**: 2023-02-22

TLDR: What are the main questions that you have/had as a beginner and what resources are you looking for but hard to find?

I am relatively new to Algo betting and have not found it easy to find good resources around modeling, statistical strategies, programming, etc.  I think that a consolidated list of all kinds of resources could benefit everyone.

I have started to keep a small list myself and would like to build it out to include a wide variety of topics. I will make it public so everyone can view it. But first I want to compile a list of Topics. What are other topics related to all things Algobetting that should be included on this list? This is what I have so far:

**Programming**

* Python/R
* Learn Python/R
* Data Scraping
* Prewritten Code Sets

**Data**

* Best resources for historical stats, box scores, Odds, etc by sport
* Best resources for current market odds
* Odds Screens
* API's

**Models and Statistics**

* Resources for Learning about statistics (particularly those relevant to sports modeling) 
* Types of Models
* Examples by sport

**Best Media Related to Sports Betting and Modeling** 

* YouTube Videos
* Podcasts
* Books
* Articles/Blogs
* Twitter Follows

**Top Comments:**

> **u/zahaha** (2 pts): Yep, I've seen this pinned post and its a good starting point. However it's lacking resources for many of the common questions and isn't organized. 

I would like to improve on this with a more comprehensive and organized list.
>
> **u/stander414** (2 pts): https://www.reddit.com/r/algobetting/comments/g5hi6j/creating_a_collection_of_resources_to_introduce
>
> **u/ENTP_Geek** (1 pts): How is this going? Have you added much to your list?
>

---

### [Where do you get football data for your algos?](https://reddit.com/r/algobetting/comments/1fiesm2/where_do_you_get_football_data_for_your_algos/)
**Author**: u/Thelimegreenishcoder | **Score**: 9 | **Comments**: 6 | **Date**: 2024-09-16

I've been scraping data from FlashFootball.com for the past year for my football predictions algo. However, the website frequently changes, causing my data API to break and requiring constant fixes. With school becoming more demanding, I no longer have the time to manage these issues. Where do you source football(soccer) data for your algorithms or models and do you have any recommendations for reliable alternatives?


I also have always wondered where does Flashfootball.com itself get the data?

**Top Comments:**

> **u/Low_Performance826** (1 pts): write me a dm i will send you a link
>
> **u/atanstef** (1 pts): Hey, I would need historical odds for football matches, where I can obtain them?
>
> **u/chiseeger** (1 pts): Missed the flashfootball part my bad. Mine was American football
>
> **u/chiseeger** (1 pts): Are you doing soccer or American football? I’ve set my own scraper up several times that will move it to your own sql db. Dm me if you’d be interested. I could probably spin it back up
>
> **u/Low_Performance826** (1 pts): if you need historical odds for soccer matches, we have nearly the same coverage as flashscore. If it is just historical odds, we could provide them for free.
>
> **u/soccer-ai** (1 pts): I've been in a similar situation myself. I've been scraping soccer data for about 3 years now and accumulated around 30,000 matches along with historical odds. The constant changes in websites like FlashFootball.com are definitely one of the downsides of relying on scraping. It's a lot of maintenance work.

In terms of alternatives, you could consider paid data sources. While they come with a cost, they can save you the trouble of frequent API breakdowns and constant scraping fixes. Platforms like Opta or SportRadar are commonly recommended, but again, they’re not cheap.

Another interesting approach is using LLM scraping—basically fetching the entire HTML and then using language models to extract the specific data you need via a prompt. It's a more flexible method, but the cost will depend on how many pages you're scraping and the size of your budget.

As for FlashFootball.com, my guess is they either use official data providers or have their own direct sources through partnerships. It’s hard to know for sure so.
>

---

### [Making NBA models](https://reddit.com/r/algobetting/comments/1e0ptxd/making_nba_models/)
**Author**: u/makingstuff237 | **Score**: 9 | **Comments**: 16 | **Date**: 2024-07-11

Hi everyone, I've downloaded every box score, quarter box score and even play by plays for every nba game and then I scraped all of the info into an sql database. I've made a few VERY basic models and would like ideas on what to do next.

My most advanced model (still super basic) takes two teams and a date (usually automated by the days schedule so it does it automatically) and spits out predicted stats for each player. I get the prediction by taking a look at stats over the past 5, 10, 20 games as well as full season, but I only look at the home or road games depending on the team. So if it's BOS at LAL I would look at Boston's past 5, 10, 20 and any game played on the road and vice versa for LA. For each of those splits (5, 10, 20, all) I get the players average stats, the opposing teams average defensive stats and the nba average defensive stats for those spans for each quarter, 1-4. I then compare the nba average defensive stats (on the road or at home, to match the team I'm looking at) to the teams defensive stats and make it a percentage. So let's say NBA average on the road allows 10 fg3a's in the first quarter but let's say Boston allows 9.5 fg3a's in the first over the same split, then my algorithm would have Boston's fg3a percentage at 95%, then I take the players averages and multiply it by the percentage to get my estimate. I do this for every stat I can. 

The program then looks at the odds which I scrape from draft kings and then compares the bet to my predicted stat and gives a confidence rating which is not impressive, it's literally just comparing my prediction to the line and then giving a bonus multilier depending on it's value, so if I show a player having 9 rebounds and the line is set at 7.5 and the over is -140 then I have a difference of 120% and then I multiply that by how far away the value is from 0, the further negative the lower the multiplier. I don't 100% remember how I did this and can't look it up on this computer right now but suffice to say it's very lacking. I have it spit out the bets it thinks are best and usually it picks about 5-10 bets per day, of those it had a pretty high ROI but the model is so simple and it needs improvement. It has obvious flaws like not being able to know who is and who isn't playing in a game among I'm sure 10,000,000 other things.


This was started as just a fun project to teach me how to scrape websites and use mysql but I'd like to learn more. I don't know about betting strategies or EV betting or anything really, I'm just 100% self taught. Any advice on what to look into would be great. Also worth noting I've only utilized full game and quarter box score information, I have not done anything with my play by play table. I've also written some code so it can identify who is on the court at any time and shows all 10 players on the court for any play and combined it with the shots data available to get the x and y coordinates of any shot taken. Here's a screenshot of my altered pbp table: https://imgur.com/a/4BxHCXW (note that it cuts off and doesn't show all 10 players in the screen shot, they're all in the table, they just didn't all fit in the screenshot.

I also have a players table with everyone's names, hand, height, weight, dob, draft info, college info, etc. As mentioned, this started out as a project to teach me python and mysql.

Everything is sourced from basketball reference and draft kings, 100% free, if anyone would be willing to help me I might be willing to share my scraping scripts.

**Top Comments:**

> **u/LawyersGunsMoneyy** (3 pts): My thought process is that the implied odds based on the line is what you need to hit to be profitable. So if there’s a line that is listed at +100, you need to hit 50% to break even, regardless of whether the line has 1% juice or 20% juice
>
> **u/makingstuff237** (2 pts): Thank you so much for the tip, I'll check it out!
>
> **u/kicker3192** (2 pts): Yes, this. De-vigging the lines only serves if you're going to utilize the books' implied probability to calculate something within the model (i.e. your model is top down and you're going to use the books' odds as a variable).
>
> **u/ezgame6** (2 pts): you still bet on the vigged odds... what you're saying is if you want to estimate your true edge? I don't see how vig free odds affect your decision making
>
> **u/makingstuff237** (1 pts): Kind of. It was a ton of work and I'm not willing to share it for free. Nor do I have a place to host it
>
> **u/fuckosta** (1 pts): Hey would you mind if I could have a look at your dataset?
>
> **u/Foreign-Procedure-91** (1 pts): Hello. Apparently it's a very interesting job.
    Does your model take into account how the absence of a player affects other players?
    For example, if a player is absent, and his individual contribution will change little. But this could have a greater impact on the game of other players
>
> **u/NarwhalDesigner3755** (1 pts): NBA API doesn't have everything, I had to merge their data with another source that I had scraped to give me a more complete picture
>
> **u/Traditional_Soil5753** (1 pts): From my experience if you use the Kelly criterion formula you don't have to worry about "de-vigging". Sports books odds can also be viewed as "% of wager returned"...ie +200 odds is just 100% of your wager returned on a win. +300 odds is just 200% of wager returned....plug this into Kelly criterion formula for your bet size and your good to go....
>
> **u/DotSlashSports** (1 pts): No problem. I'd listen to some of the Spotify podcasts with the person who did DARKO. His name is Kosta. I'm sure you will get some good nuggets of info from them.
>

---

### [Best place to get historical esports (CSGO) odds](https://reddit.com/r/algobetting/comments/10yu2mf/best_place_to_get_historical_esports_csgo_odds/)
**Author**: u/goatcs | **Score**: 8 | **Comments**: 8 | **Date**: 2023-02-10

Hello,

&amp;#x200B;

To practice my python skills I want to create a model that will try and predict pro csgo games. I was wondering if anyone has a good source for historical odds as I am not really finding anything particularly useful in my searches.

Furthermore, does anyone have any good sources for csgo data in general, I am aware of HLTV api on github [https://github.com/gigobyte/HLTV](https://github.com/gigobyte/HLTV).

&amp;#x200B;

EDIT:  


Ideally I would like a full dataset of the last 2 years games, showing the map, the 2 teams that played, if it was lan or online, the odds for each map (odds for other things like rounds etc. would be amazing), who won, the date it was played, the score at half time, the scoreboard (at half time as well would be awesome). I should be able to get most of this through the hltv api but if anyone has any suggestions or better ideas that would be great because getting all this data will be time consuming.

&amp;#x200B;

Thanks in advanced.

**Top Comments:**

> **u/Ok-Seaworthiness3874** (2 pts): sure! and check my edit on the previous comment about scrapers. I think that's ur best way to start collecting data realistically. I used to make web scrapers in my past job so if you need any pointers lmk. I think selenium library is also really good if you want to stick with python.
>
> **u/Ok-Seaworthiness3874** (2 pts): I do a lot of Dota 2 esports betting, like 10k a week in bets placed - and I have thought about trying to do something similar with Dota open api data. I do wonder how useful 2 year old data actually is for any E-sport. At least with Dota, there are very tranforming updates that release ever 3 months or so, that kind of nullifies old data as it relates to win probability with certain heroes and whatnot.

Also, rosters change VERY frequently in Dota. Usually 1-2 times per year, rosters will change either a couple players or the entire team. I wonder if it's the same with CS:GO, where data from even a year ago would provide little to no insight into their current strength as a team.

If such is the case with CSGO as it is with Dota 2, I would focus on much more recent data. I find with e-sports in general teams go on very hot streaks, or they play well in against certain regions while playing poorly against other regions. THis could have more to do with the heroes that certain regions tend towards, and how those micro-meta's clash when in Major LAN matches. I know a lot of CSGO meta revolves around the $$$ made between rounds, and how that might help certain teams who battle better with certain weapons or whatever. It might be worth considering like what is their probability of winning with less gear, vs more gear for a given round, on a given map, vs a given team. Some teams might be trash at pistol round but insane if you give them an AWP (I don't really follow GO closely, so I wouldn't know).

But in general, I'm not sure 2 year old data would be helpful. It's a different game, with different meta, and different team rosters I would reckon.
>
> **u/Gurubusters** (1 pts): You can get free 1 minute odds data at [https://historicdata.betfair.com/#/home](https://historicdata.betfair.com/#/home) if you have a betfair account. It should be in 'Other Sports'. For more advanced data, you'd have to pay.
>
> **u/goatcs** (1 pts): what do you believe the 2 big meta shifts were? I know there have been map changes and changes to the M4 but I don't believe these were massive meta shifts, unless I am missing something.
>
> **u/ScooobySnackks** (1 pts): CS has has 2 massive meta shifts over the past year and a half. You’re going to need to segregate any map level data between the 2 metas. Otherwise you’re gonna miss the mark
>
> **u/goatcs** (1 pts): thanks, i will take a read of these
>
> **u/Ok-Seaworthiness3874** (1 pts): That's true - Dota is a lot more teamwork intrinsic, where the hero you pick is reliant on what your teammates pick and are good at. Making one player with his specific hero pool, maybe a poor fit in general for a team that can't support it. Where CSGO players can essentially perform mostly the same on different rosters.

I know i've been able to find a few Dota 2 win probability doctoral thesis' online just by searching. You could maybe search for something similar for CS:GO to see if somebody has published a journal about it that could lead you in the right direction.

Here's one I found for you: [https://dspace.cvut.cz/bitstream/handle/10467/99181/F3-BP-2022-Svec-Ondrej-predicting\_csgo\_outcomes\_with\_machine\_learning.pdf](https://dspace.cvut.cz/bitstream/handle/10467/99181/F3-BP-2022-Svec-Ondrej-predicting_csgo_outcomes_with_machine_learning.pdf)

&amp;#x200B;

[https://publications.lib.chalmers.se/records/fulltext/256129/256129.pdf](https://publications.lib.chalmers.se/records/fulltext/256129/256129.pdf)

&amp;#x200B;

[**https://osf.io/u9j5g/download**](https://osf.io/u9j5g/download)

My guess is some web scraping will absolutely be needed to pull this off. Building a web scraper is quite easy - and you can use ChatGPT to help. For instance, say in ChatGPT "Create a web scraper using puppeteer (A JS library I use) that stores the value of element \[figure out what this element name is using a chrome plugin or whatever\] every \[time interval\] or everytime the element changes". That should get you started. Then you'll have to think creatively about how you plan to sync those odd's with the actual game time. YOu would likely need two scrapers running side-by-side, one that's pulling odds, and one that's pulling current match data. (real-time, as I know dota has a 5 minute delay on stream, but a 1 minute API delay that books use to create odd's in a algorithm - check [hawk.live](https://hawk.live) if you want to know what I mean). Basically Dota 2 servers can [...]
>
> **u/goatcs** (1 pts): I agree with you, esports moves very fast compared to the typical sports so in my opinion 2 years data in csgo may not be as useful as 2 years data in football. I wanted to start with a 2 year dataset so I can do tests and see if old data will have impact.

I don't really know much about Dota but in CSGO there aren't really any transforming updates (at least in the last 2 years), the biggest updates are often just a new map in the map pool with an old map being taken out, this should be fairly easy to track as you can easily filter out maps not in the map pool.

Roster changes is something I will need to take into account and I agree 2 years roster data will show very little insight as teams can completely change multiple times in that time span. However, I believe 2 years data will be more useful for individual player stats as the game hasn't changed enormously in that timespan. So hopefully 2 years data will show some insight into player strengths.
>

---

### [Soccer Value Betting Team](https://reddit.com/r/algobetting/comments/120mki5/soccer_value_betting_team/)
**Author**: u/AssignmentHelpful | **Score**: 8 | **Comments**: 8 | **Date**: 2023-03-24

Hey pals, I’m looking to build a small team (3-5 people) to develop a system to price the following soccer markets: moneyline, over/unders and Asian handicaps. 

I recognize the difficulty in pricing soccer given the popularity of the sport, the high cost of data and the competition from big betting syndicates, but I believe there are pricing inefficiencies that we can exploit using feature engineering on event data. The development of the infrastructure will most likely take between 5-10 months with the right people. I have already tackled some of the scrapping and data wrangling required, but I’m still far from having a streamlined system.

The project will entail:
- Scrapping and cleaning event data (started)
- Scrapping and cleaning odds data (started)
- xG, xThreat model implementations (started)
- Feature engineering 
- Developing machine learning modes
- Testing accuracy of the models
- Deploying everything to servers/cloud

This should be a fairly big project, so I don’t expect many of you to be interested. 
The worst case scenario is that we don’t find any edge, if that’s the case we would still have the infrastructure to do any other projects regarding soccer. 

Let me know if you are interested or if you are just curious about the project and it intricacies.

PD: I’m coding in python and storing data in SQL

**Top Comments:**

> **u/TheBigLT77** (1 pts): New to algo but ten years betting on soccer and played at a high level. Happy to help
>
> **u/yungreseller** (1 pts): I’d recommend a different sport, if you print the premium free pinnacle odds against the odds implied by results, you usually find that if there are mispricings they are usually covered by the bookies premium. I mean think about it, in this market alpha can only exist for you, if you are the only one knowing it.
>
> **u/AssignmentHelpful** (1 pts): The idea would be to develop models that beat the closing line on sharp bookmakers (pinnacle and betcris), so that you can consistently bet sizeable amounts on these sites without the danger of getting restricted or banned. Way easier said than done, but I’m certain that it’s achievable on some markets.
>
> **u/boardsteak** (1 pts): How do you expect to capitalize on your results?
>

---

### [My attempt at a model to bet on NFL games](https://reddit.com/r/algobetting/comments/ggaz71/my_attempt_at_a_model_to_bet_on_nfl_games/)
**Author**: u/HamirTime | **Score**: 8 | **Comments**: 14 | **Date**: 2020-05-09

Hey guys, been lurking since this subreddit got created and knew I would be contributing to it once I got my model to an "acceptable" state to hopefully get further insight.

Gonna try to keep this as short as possible because alot of explaining happens in the Jupyter notebook, but here goes.

So basically I took a data mining course this last semester and the final project was to apply the concepts we learned in class to a real world scenario. While the NFL was in full swing, I was a frequent sports better and would really enjoy betting and watching the games. Data and modeling still seemed like such a complex topic to me, but I knew that eventually I would the subject either in class or on my own. After learning the data mining world, this in-class project was a perfect way to test what I had learned as well as try and use my skills to make some money.

SO with all that out of the way, the summation of the actual data and models is that I took game data from Kaggle (mainly used to pull the scores) and added full team rosters for both away and home teams (rosters scraped from another site). My thought was that since each team is composed of 52 players, that at the end of the day their performances (with the leadership of the head coach) is what determined the outcomes of the game. So to summarize, each of my records contained the home and away teams, current W-L records, and most relevant positions for both teams. I also decided to filter the data to only be within this millennia.

With this data I tried to use regression models to predict the score of the games. This score would then be compared with the vegas spread for that game so that the model could predict whether it should bet on the home team or the away team to cover the spread. This might not be a good practice, but I just decided to use every game from the 2000-2018 season to predict 2019 games as my model testing phase. I used the SVM Regressor algorithm (primarily because it was the only one that supported unbalanced data, which is obviously important since the more recent games should play a bigger factor) and an Artificial Neural Network because it's pretty easy to grasp and honestly doesn't require much thinking or work from me. Kinda also used it in case I was configuring the SVM wrong.

In summary, my results were slightly worse than I was expecting.  Both my models average out to about 52% accuracy and a mean squared error of around 195 when compared to the actual point values. Hence the main reason I am posting here: to get some help from more experienced data scientists.

I've decided to include my work here, both for more experienced people to critique and maybe for some less experienced people to learn. This project was, again, done as a school project so please excuse some of my markdown comments as they had to follow a format for the class. This is also done in Python primarily using scikit learn for all data modeling and pandas for pre-processing. I used VS Code as my IDE with the Microsoft Python plugin to view and edit Jupyter Notebooks.

I want to keep developing this in the future, at this point not even to make money but just because I think it's a cool concept. The thought of math being able to better predict as complex a game as football more accurately than almost anyone is crazy. Other than this model, I recently also purchased a Raspberry Pi (also being used for other side projects) to eventually automatically pull new game data for the model to predict.

Like I said above please feel free to critique, this was basically my first major python project and I had no experience with any of these libraries. Also don't usually post on Reddit so if my formatting sucks call me out on that too.

Thanks guys, hope this is a helpful post to keep the subreddit going.

Jupyter Notebook: http://www.filedropper.com/finalproject_2 (not sure how long the site will host the file TBH)

**Top Comments:**

> **u/15woodsjo** (4 pts): To piggy back off this answer, I would also throw in a suggestion of using a neural network and turning this into a binary classification problem.

In practicality this is a logistic regression model that you have more control over, and can potentially get a little bit better of a model out of the algorithm.

&amp;#x200B;

The reason I would suggest anything binary classification for this type of problem is you would want to be able to measure the % likelihood of one team vs. another covering the spread whilst the line moves. In essence, you can get more information by knowing that team A has a 60% likelihood of covering a (-9) line and team B has a 40% chance PLUS team A has a 55% likelihood of covering a (-10) line and team B has a 55% chance. Basically you want to be able to apply your model to a dynamic line to get what is hopefully a more accurate picture of a +EV game
>
> **u/KidMcC** (3 pts): Will respond more fully later, but one thing that jumps out at me is that you might want to explore using a GLM with Poisson distribution as opposed to something like SVMs for football scores. This allows you a better probability assignment to different outcomes. 

Basic googling should land you more stats-focused details on that.

As an aside, there are better ways to handle imbalanced data than using an SVM for assigning binary winner/loser status. SVMs rarely perform consistently better than some other such models, like Logistic Regression or Random Forest Classifiers. Looking into weighted logistic regression or sub-sampling to balance out data as opposed to picking a specific model family as a result.

&amp;#x200B;

Again, will respond more later, as it's an interesting problem. Also open to debate re: any of the above.
>
> **u/15woodsjo** (2 pts): That's fair, my background is in basketball where I suppose there is a larger sample size.
>
> **u/KidMcC** (2 pts): This is a very important distinction. "Binary classification" can be done at least two ways here.   
1) Linear model (of sorts) fit to predict the point difference (homeScore - awayScore). Again, GLM approach with Poisson Distribution is the most common choice for football for a reason, given how scoring is not linear with each point-accumulating event. The sign of the endogenous variable would then be indicating the "win" the same way a 1/0 would in your example. Here you can use size of the difference to indicate probability, to some degree.   
[https://www.sbo.net/strategy/football-prediction-model-poisson-distribution/](https://www.sbo.net/strategy/football-prediction-model-poisson-distribution/)

[https://www.pinnacle.com/en/betting-articles/Soccer/how-to-calculate-poisson-distribution/MD62MLXUMKMXZ6A8](https://www.pinnacle.com/en/betting-articles/Soccer/how-to-calculate-poisson-distribution/MD62MLXUMKMXZ6A8)

2) Ignore points and predict an actual binary variable indicating whether or not the home team won. What this modeling approach provides is a direct probability associated with each classification. This also requires a choice to be made of regularization, L1/L2 penalty if using Logistic Regression, etc.  


Predicting scores via regression, and then daisy-chaining that back into a spread comparison to then take advantage of error profiling, like you said, is quite indirect and will certainly introduce more bias and/or volatility than what it returns in accuracy.
>
> **u/KidMcC** (2 pts): If we are talking about predicting binary game outcome, then I'd be hesitant to go the route of neural network. By its very nature of scheduling and season construction, football doesn't offer a huge dataset of games to really draw from (compared to other sports). Especially if you aren't weighting games from the distant past fairly, one can find themselves with a high variance, over-parameterized model fit on too little an amount of data. All my opinion of course! 

I do think a thoughtful feature selection process fit to an XGB or RandomForest model might be more manageable given that gameplay data gets old fast. Exponential weighting can be your friend here, though, if you need to go way back, just make sure your offense-profiling is dynamic!
>
> **u/15woodsjo** (2 pts): You are implementing a binary decision based on your model but not using an algorithm that is trained using binary classification. Slight difference
>
> **u/HamirTime** (2 pts): Thanks for the insight, I will definitely look into GLMs and their applications. I'm more familiar with logistic regression, so I would probably err towards looking into that to better handle imbalanced data
>
> **u/HamirTime** (2 pts): I could be misunderstanding your suggestion, but I think I am currently already transforming this into a binary classification problem. After using regression to calculate the score, I compare it with the spread to calculate a 'class' variable (0 or 1). 0 meaning a bet should be placed on the away team and a 1 meaning a bet on the home team. I use these to also measure common metrics like accuracy, precision, and recall.

 The likelihood percentages was also something I wanted to implement by using the difference between the predicted score and the spread, but wanted to focus on improving the model before then
>
> **u/anxiousalpaca** (1 pts): You are right, i totally misread what is meant by daisy-chaining back (not an English native speaker)
>
> **u/KidMcC** (1 pts): The OP said nothing of features describing the relative defensive capability of either side of the ball. Without such features, I'd still say daisy-chaining yhat values for score back into a comparison is risky, as it leaves nothing in the model reflecting the fact that for one team's offense to have the opportunity to score, it generally requires that the other team does not have the same opportunity at the same time (save for pick-6s). Volatility would be unstable when you begin to use this approach with games where disparity between defensive capability on each side is substantial. At least, this is what I have found. Curious to hear more if this is still at odds with your experience.
>

---

### [The benefit of new coding methods in AI for peoples with limited skills in programing. A journey to get your data for sports betting analysis.](https://reddit.com/r/algobetting/comments/1j9n0ri/the_benefit_of_new_coding_methods_in_ai_for/)
**Author**: u/schnapo | **Score**: 7 | **Comments**: 0 | **Date**: 2025-03-12

I recently tackled a personal project to scrape a large set of sports data from a website—thousands of lines’ worth—and transform it into a format I could analyze. Normally, I’d spend days or even weeks juggling various scripts and debugging each step. But this time, I brought AI into the mix, and it made a world of difference. Here’s a quick overview of the process, without going into the nitty-gritty of the actual code:

I outlined my goals to an AI assistant: gather data on games, teams, and statistics from a particular sports site. The AI helped me piece together a basic approach—where to send requests, how to parse the pages, and what columns I might need.

Once I had a rudimentary script, I hit typical obstacles like missing data fields, date mismatches, and odd formatting. Each time I encountered a snag, I described the issue to the AI and got suggestions on how to fix or streamline the process. It was like having a coding partner who never sleeps.

After a few rounds of refinement, I could easily loop through a range of dates and collect thousands of lines of game data in a fraction of the time it would normally take. The AI offered best practices along the way—like how to handle inconsistent naming conventions and how to merge data sets without losing rows.

In just a few hours, I had a robust data set ready for analysis. Where I might normally spend days doing trial-and-error debugging, I now had a near-automated pipeline. It was a massive time-saver and a huge motivator to tackle more complex data tasks in the future.

  
If you’re thinking about diving into web scraping or data collection, consider bringing AI assistance into the process. It won’t do all the thinking for you, but it can drastically cut down on the time you spend wrestling with small, repetitive hurdles. It’s a perfect way to focus on the bigger picture—like deciding how to use all the data you’re collecting—rather than getting stuck on every little detail of the code.

  
For example: I have never worked with Python before, only with R. Now I have a full scraper ready which captures lines, ratings and data within minutes. It is not something to brag, just motivate others to do the extra work.

---

### [NFL Play by Play Data](https://reddit.com/r/algobetting/comments/zlf6xu/nfl_play_by_play_data/)
**Author**: u/mxx24 | **Score**: 7 | **Comments**: 2 | **Date**: 2022-12-14

I've been looking for some more advanced play by play data for a new system, NFL fastr and its python equivalent have personnel and men in box frequencies, but I am looking for something containing the specific man, zone, and type of zone (2-high shell for example) for each play as well.   I've seen various users tout these percentages on Twitter, but cannot find a proper dataset to show for it. thanks.

Edit: I also build out various quant betting models for other sports, have been working on football as of late, happy to partner up if interested

**Top Comments:**

> **u/Louisville117** (1 pts): I tried for a while to see if AWS offered any of its data but sadly no. Would be great even if I had to pay for it. Tons of data in there.
>

---

### [Looking for partner on CS2 betting project](https://reddit.com/r/algobetting/comments/1k76y3q/looking_for_partner_on_cs2_betting_project/)
**Author**: u/Stepanovich | **Score**: 6 | **Comments**: 0 | **Date**: 2025-04-24

Hi Team, will keep this short and sweet but I am looking for someone to pair up with on creating a betting syndicate for CS2. I am developing the trading platform using C# and will bet through Sport market API. If you have experience in C# and data science and want to be involved in this project, get in touch.

---

### [NFL Passing Attempts Model Advice](https://reddit.com/r/algobetting/comments/1k67adj/nfl_passing_attempts_model_advice/)
**Author**: u/toddinvesterguy12 | **Score**: 5 | **Comments**: 7 | **Date**: 2025-04-23

Hey everyone, I just tried for the first time to build a model that predicts a players pass attempts. I collected 3 years of data via scraping/APIs with columns formatted as 

Date of game,
Player,
Pass attempts in game,
Players team at time of game,
Home/Away,
Opponent team,
Player’s Coach,
Game start time,
Location of game,
Average temperature during 4 hours from start of game time,
Type of precipitation if any,
How many hours in four hour window precipitation occurred,
Pre game points total at fanduel and DraftKings,
Pre game total odds at fanduel and DraftKings,
Pre game spread for players team at fanduel and DraftKings,
Pre game spread odds for players team at fanduel and DraftKings,
Pregame pass attempts total at fanduel and DraftKings,
Pregame pass attempts odds at fanduel and DraftKings

I have minimal experience with coding (2 intro level courses in python and R), so I loaded this data into Claude and promoted it to create linear regression and random forest models with the data. I prompted it to train on half and test on the other half. Both achieved an r2 of around 0.4 so not good. 

At this point, I’m curious if I’m trying to predict a metric that is too volatile, if I need more data using the same features, if I need to add additional features, a combo, or if I’m missing something else I should learn about before proceeding. 

Appreciate any advice.

**Top Comments:**

> **u/cortezzzthekiller** (6 pts): Props are generally about predicting volume -- and passing attempts is ALL about volume. So you are missing a huge part of the puzzle here -- off/def plays per game
>
> **u/2kungfu4u** (2 pts): Huge agree here. I'd also argue in tandem with that you'd mostly likely want to include metrics like pass rate over expectation, pass rush splits on a given team and maybe even team record. It's one thing to include the spread indicating if they're a dog or not but how often they are a dog is valuable as well imo
>
> **u/Golladayholliday** (2 pts): I mean… What is the point of this model? To beat the books? To do some learning? 

You included the book odds, any good model is just going to violently latch on to that with the other things you have included(missing some major pieces). You very likely have built a devigger 😂. This is where the journey starts tho. Keep on pushing. 

I think the best piece of advice I can give you is what I wish someone had told me. ML/AI isn’t magic, it’s an extension of your expertise. You can huck a bunch of data at a model and you might get a okay baseline, but that is not what makes a model great. You need the domain knowledge and ML knowledge to know what is important and how to present (feature engineer) it, and if done right it will come to very similar conclusions as an expert would. 

The difference is it can do it in less than a second instead of an in depth time consuming expert review. That’s the magic.
>
> **u/Golladayholliday** (1 pts): It’s going to be tough only because you’re essentially feeding a much better model back into your model as an input that’s likely considering all the same things you are plus a lot more. 

The other thing to accept is most bets there is no +EV side. I have a very solid baseball model, and if I had to estimate about 80% of the time I get some number that’s between the spread(both sides lose money long term), 10% it’s very light value (picking up a quarter or 2 of EV on my $50 bet) and 10% it’s decent.
>
> **u/toddinvesterguy12** (1 pts): Essentially I want to connect the predictions it makes to +EV sides on passing attempt bets. For now I just need to learn more about machine learning and how best to present data to these models and I really appreciate your insights
>
> **u/toddinvesterguy12** (1 pts): Appreciate it that’s a great idea
>

---

### [Universal Kelly Calculator](https://reddit.com/r/algobetting/comments/1k0pgyt/universal_kelly_calculator/)
**Author**: u/vegapit | **Score**: 5 | **Comments**: 8 | **Date**: 2025-04-16

Hi there,

I have worked on an algorithm to find the optimal Kelly fractions for the most general use case i.e. multiple simultaneous independent bets each with multiple exclusive outcomes. Its inner workings are briefly described in this short article on my [blog](https://vegapit.com/article/universal-kelly-calculator). You can also directly give it a try [here](https://vegapit.com/kellycalculator).

Have a great day

**Top Comments:**

> **u/vegapit** (1 pts): To be clear, my claim is just that it is a good compromise between accuracy and speed of convergence for this very SPECIFIC case. Not much else, really.

I have exported the Rust algorithm to a Python module, so benchmarking should be easy to set up.
>
> **u/statsds_throwaway** (1 pts): i thought clarabel supported exponential cone programs
>
> **u/vegapit** (1 pts): Yes, speed of convergence. I am not familiar with Clarabel, but reading the doc, I don't think I could use it for 2 reasons:

1. My objective function is not quadratic. I can apply a taylor expansion to make it approximately so, but this would be wrong for certain bet parameter values.
2. It does not handle bounds on the decision variables at the local or global level.
>
> **u/statsds_throwaway** (1 pts): fair play, your last paragraph clears up things nicely

regarding your point about general tools, what do you mean by performance? as in runtime? i would be surprised to see a significant enough gap between your implementation and a solver like clarabel
>
> **u/vegapit** (1 pts): There are open source solvers for convex problems available in Rust. I plan to benchmark the current solution with one.

Otherwise, open source is indeed great but from experience, using very general tools to solve specific problems is often not optimal for performance.

There is no paywall at the moment. Just me limiting the computing load on my server by reducing the input data size =:D
>
> **u/statsds_throwaway** (1 pts): i see, that's an interesting rule. i've read your write-up before on using gradient ascent so would be interested to see how it holds up against more direct convex opt algorithms such as interior point methods
>
> **u/vegapit** (1 pts): Thanks, my algo is in Rust, and my general rule is to avoid third-party dependencies if possible. It could be useful to benchmark it against, though.
>
> **u/statsds_throwaway** (1 pts): you can do this pretty easily with CVXPY
>

---

### [Programmer looking to get started](https://reddit.com/r/algobetting/comments/1gaitzp/programmer_looking_to_get_started/)
**Author**: u/racerx1036 | **Score**: 5 | **Comments**: 4 | **Date**: 2024-10-23

I am a programmer by profession but want to get into algo betting. I work with PHP by way of trade, but have dabbled in python before would definitely need to learn some stuff there as I go though. Whats the best way to get started building an algo im thinking of starting with NBA stats since they seem to be relatively predictable and reliable. I figure doing Overall game stats would be easier to start than including player props like ppg etc but I do want those down the line. I want to as I learn more be able to build this into quite a complex model. What is a good starting point / places to research or watch, first kind of model to build etc. So for NBA what would be some principals to learn to build this model. Any tips appreciated. Thanks!

**Top Comments:**

> **u/Governmentmoney** (1 pts): There are many ways to do things, if you're going down the ML route you can get some ideas from here: [https://betfair-datascientists.github.io/modelling/howToModel/](https://betfair-datascientists.github.io/modelling/howToModel/)

Pretty basic stuff but it will give you a direction to move towards and experiment
>
> **u/__sharpsresearch__** (1 pts): nba_api is was faster than scraping. it will save you days.

pandas/sklearn/numpy should be all you need on the modeling front for the most part

decision trees are very common, our model that is currently running on our site is using a light gradient boosted tree
>
> **u/racerx1036** (1 pts): Thinking of just web scraping something and playing around with pandas and decision trees but not really sure what to do there so I’ll have to do some researching. But yeah like u say to start simple but when I’m ready for more what direction do I head?
>
> **u/__sharpsresearch__** (1 pts): good picks on nba, high level team stats btw.


nba_api is great. join their slack.

initially, make a db, grab everything from ~2008-2010 and throw it in a team, player, match, boxscore table. or something similar so you can fuck around and not get rate limited.
>

---

### [Types of stat/cs college classes for better intuition and knowledge for sports modeling?](https://reddit.com/r/algobetting/comments/1fnnvho/types_of_statcs_college_classes_for_better/)
**Author**: u/GeometricBison9 | **Score**: 5 | **Comments**: 7 | **Date**: 2024-09-23

Hello, I am a college student studying essentially a dual degree in CS and Stats. I’ve been betting for 7 months through a discord and have an 18% ROI on pikkit. I am very interested in trying to beat the books using my own data analysis and modeling. For those who have this background, what types of classes are important for this type of work? I know a huge part of finding edges is analyzing Sportsbooks odds and EV, but I was wondering what type of statistical stuff is good to take?
I have pretty solid CS knowledge and can learn stuff pretty quickly, and I already have done quite a bit of web scraping, web dev, and basic ML with scikit and PyTorch.

My repertoire: stat modeling, lin alg, calc3, stats and prob, stochastic processes, data structures, artificial intelligence

Any advice is greatly appreciated!

**Top Comments:**

> **u/__sharpsresearch__** (11 pts): The biggest hurdle i see everyone here with is the fact that ~~no one can~~ most people cannot program properly. You will be able to move faster and learn more than anyone if you can understand how to create a psql database and stand up a server on digital ocean.

programming is 95% of the work to be good at algobetting. Most "AI" in algobetting is best done with xgboost, logistic or linear regression so know these really well, calc/advanced datastructures are borderline useless.

Learn as much about feature engineering as you can.
>
> **u/jbr2811** (4 pts): To piggy back off of this, scraping lines and stats and managing a database of all that info is a huge part of it. Focus on programming first of your intention is to originate your own numbers.
>
> **u/Shallllow** (2 pts): It's not a be-all end-all, just more flexible. I'd wager the best DL people are better than the best LGBM/XGBoost people, but the median case is better for boosting. Not sure what your point is with the latter, some other kind of model?
>
> **u/fysmoe1121** (2 pts): and not getting IP banned for web scraping off sites you’re not suppose to lol
>
> **u/Mr_2Sharp** (1 pts): Strangely enough feature engineering wasn't taught in any of my classes but it's basically the most important part imo. You can have chatgpt get you 80% through to running a model in Python the rest will take you anywhere from 20 minutes to an hour depending on your experience. Feature engineering on the other hand is an entirely different beast and can take enormous amounts of time from gathering, organizing, and cleaning data to having the mathematical maturity and insight to create your own features. This is expedited by having programming skills as others here have said. So definitely learn to feature engineer in some programming language. As to which language is optimal is anybody's guess.
>
> **u/KolvictusBOT** (1 pts): Doubtful deep learning is the be-all end-all answer. I did not mention deep learning on purpose. But you can go beyond dumping csvs into xgboost. And in the future, I highly doubt that that(xgboost) will in any way provide you an edge over the market as a small-time operation without data that others lack.
>
> **u/Shallllow** (1 pts): Models can only be as complex as the amount of data you have, high frequency trading? Sure, deep learning is gonna be on top. Betting on 10s or 100s of games? Having a solid understanding of fundamental stats, good prior assumptions, and quality data is much more important.
>

---

### [From Simple Models to Market Analysis: Is It Even Worth It?](https://reddit.com/r/algobetting/comments/1i7c0ma/from_simple_models_to_market_analysis_is_it_even/)
**Author**: u/National-Yogurt7021 | **Score**: 4 | **Comments**: 5 | **Date**: 2025-01-22

Some time ago, I started collecting historical data from football leagues and built a simple Python script. The script searches for teams in future matches based on specific criteria and finds teams with similar characteristics in the historical data. From a larger sample of the identified matches, it derives win probabilities and odds. I initially tested it with just one criterion, namely the average points per game. In the backtest, this resulted in a -12% yield, which didn’t surprise me, as it was extremely rudimentary. In that sense, it was amusingly a good contrarian indicator, so I tested a betting strategy based purely on randomness in the backtest. Even that performed better with a yield of -8%, lol.

I then planned to implement additional metrics to refine the model but decided instead to test the model provided by the site [xgscore.io](http://xgscore.io) by creating a Blogabet account. The reason was that I thought the approach used by the site seemed very sophisticated, and I probably wouldn’t be able to do better. On Blogabet, after 416 bets using their odds, I am currently at a yield of -7%. The sample size isn’t that large yet, but I find it hard to believe that it will improve significantly over time. The average odds are 2.318 (43%), with a win rate of 42%.

As of now, this would imply that the market odds (all bets placed on Pinnacle) pretty much reflect the actual win probabilities. This raises the question of whether it’s even worth pursuing such a project further, given how efficient the market seems to be. Respect to everyone who has managed to build a profitable model in these markets.

---

### [NBA player prop stats scraping](https://reddit.com/r/algobetting/comments/13w2no6/nba_player_prop_stats_scraping/)
**Author**: u/fiachrah98 | **Score**: 4 | **Comments**: 4 | **Date**: 2023-05-30

Hi,
I’ve been running a player prop betting system for NBA since start of conference finals but it consists of me going to different websites and copying and pasting info every day.

These are the website I need a way of extracting the table from into a google sheet.

Any help is appreciated.

https://www.nba.com/stats/players/traditional?PerMode=Totals&amp;LastNGames=5

https://www.lineups.com/nba/nba-player-minutes-per-game

System after conference finals:

Bets: 121
Profit: 22.71u
ROI: 14.6%

---

### [scraping python](https://reddit.com/r/algobetting/comments/1jtwwga/scraping_python/)
**Author**: u/Helpful_Channel_7595 | **Score**: 3 | **Comments**: 13 | **Date**: 2025-04-07

hey yall any tips on how to scrape with python hard sites that detect bots and all kind of stuff im trying to scrape prizepicks there plays , players, line stats all that kind of stuff i’ll love to read yall opinion &amp; recommendation

---

### [NBA scores predicting](https://reddit.com/r/algobetting/comments/1flxcib/nba_scores_predicting/)
**Author**: u/FireDragonRider | **Score**: 3 | **Comments**: 26 | **Date**: 2024-09-21

Yesterday I finally invented a way to predict NBA games. Maybe 🤔 

I use NBA API, calculate some averages, then I ask GPT about them, then create some embedding vectors, then logistic regression. In the end I have probabilities of a team scoring more than each possible score plus minus 20 from the real score. So the first 20 should have a higher probability of "more", the second 20 should have a higher probability of "less". 

What do you think is the best way to test this algorithm? What metrics should I use to test it well and either against bookmaker predictions or at least against real scores, comparing the average accuracy to bookmakers?

---

### [the-odds-api for historical live odds reliable?](https://reddit.com/r/algobetting/comments/1kb4htn/theoddsapi_for_historical_live_odds_reliable/)
**Author**: u/[deleted] | **Score**: 2 | **Comments**: 6 | **Date**: 2025-04-30

---

### [Looking for a good pre match odds api for soccer](https://reddit.com/r/algobetting/comments/1k65m3u/looking_for_a_good_pre_match_odds_api_for_soccer/)
**Author**: u/Strong_Plant_4545 | **Score**: 2 | **Comments**: 7 | **Date**: 2025-04-23

Hey

I am looking for a reliable odds api for pre match odds for soccer. I need one that is frequently updated and includes many bookmakers from EU. Do you know any and do you know the prices?

---

### [Data source (API) - Arbitrage betting](https://reddit.com/r/algobetting/comments/1fn851s/data_source_api_arbitrage_betting/)
**Author**: u/OogyBoogyMen | **Score**: 2 | **Comments**: 3 | **Date**: 2024-09-23

Hi, I am currently collecting data over a specific online Casino, CloudBet, in oprder to test some arbitrage strategies. They give access to their API for free which makes itt super easy to gather whatever info I need.

I am looking to collect the same data but from other SportsBooks to compare the odds the provide and the volatility of their changes. 

Would anyone be able to suggest me or would have already tested another API to some other bookies?

Guidance would be appreciated since all these API that pop up online for eg. Bet365 seem old and they all cost money, so I don't want to end up paying for something that's not up anymore.

Thank you all

---

### [Anyone know the status of MySportsFeeds.com?](https://reddit.com/r/algobetting/comments/105q4et/anyone_know_the_status_of_mysportsfeedscom/)
**Author**: u/postrema19 | **Score**: 2 | **Comments**: 4 | **Date**: 2023-01-07

Hi All.  Long time lurker/first time poster.  I have a background as software developer and am very interested in this space, but am finding it difficult locating a good source of historical data and/or feeds.

I  recently stumbled across what looked to be a promising API provider at [MySportsFeeds.com](https://MySportsFeeds.com), but have found them to be unresponsive.   The API and data modeling seem to be pretty mature and well organized, but I recently found that it is not returning data for NCAAM basketball, so I'm beginning to wonder if this site is now defunct.

Does anyone have any insight into the status of this provider?  If not, any recommendations in terms of other providers in this area would be well appreciated.  I am primarily interested in data for the "big four" of the US (NFL, MLB, NBA and NHL) as well as college basketball data.

Any help or direction is greatly appreciated!

---

### [Fractional Kelly Criterion approaches?](https://reddit.com/r/algobetting/comments/m7lknn/fractional_kelly_criterion_approaches/)
**Author**: u/simiansays | **Score**: 1 | **Comments**: 18 | **Date**: 2021-03-18

Hi, do folks here use the Kelly Criterion? Just wondering what approaches you use for translating a Kelly number into an actual allocation.

At the moment, I'm just doing a 15% fractional Kelly but wondering if anyone has spent much time tuning Kelly-based allocations. I vacillate between thinking 15% is too agressive or too conservative. Most of my positions end up being around 1-5% of bankroll. I picked this number to minimize drawdown risk but am toying with the idea of increasing it slowly as the bankroll grows and I get a better feel for the model.

I'm also moderating my model's perceived edge to reduce the instances of huge Kelly recommendations - at the moment, I'm just chopping all perceived edge in half which feels about right.

The main drawback I see right now is that it feels like I'm under-allocating the rarer longshots where the perceived edge is large, and based on my results the real edge was also large but the Kelly recommendation for those plays using this system was very small (usually \~1% of bankroll). Curious if anyone has encountered the same thing.

This article was the most mathy one that I could still (mostly) absorb on the topic: [https://caia.org/sites/default/files/AIAR\_Q3\_2016\_05\_KellyCapital.pdf](https://caia.org/sites/default/files/AIAR_Q3_2016_05_KellyCapital.pdf)

---

### [Odds Screen Recommendations?](https://reddit.com/r/algobetting/comments/113kr7r/odds_screen_recommendations/)
**Author**: u/zahaha | **Score**: 1 | **Comments**: 7 | **Date**: 2023-02-16

Anyone have a good odds screen that is either free or reasonably priced? The more features the better but it doesn't have to be overly complex. At the minimum I need up to date lines from the legal books and it has to include Tennis. 

Right now I am getting robbed by Oddsjam and will be cancelling my subscription this month. I like Betstamp. It is great for a free tool but does not have as many features as OddsJam. Ideally, I want something that I can easily pull into excel. A free API would be ideal. Bonus points for a site that shows low hold and arb opportunities. Would like to have live lines but don't need them.

---

## Results, ROI & Profitability

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [A tool for analysing odds](https://reddit.com/r/algobetting/comments/yd86kl/a_tool_for_analysing_odds/)
**Author**: u/_rbp_ | **Score**: 13 | **Comments**: 8 | **Date**: 2022-10-25

I have created an application for analysing odds – [www.rationalbets.com](https://www.rationalbets.com). It allows to identify profitable sports bets using the concept of expected value. I would be very grateful if you could check it's handy and provide feedback.

All you have to do to use it is:

· Choose an event from the sidebar or add a custom one.

· Set the probabilities of the event outcomes to your best knowledge using intuitive sliders.

Based on the probability distribution you specify, the tool will calculate the expected profits of your picks.

The tool is regularly updated with odds for football, NFL, baseball, and basketball. There is also an article section on maths in gambling.

www.rationalbets.com

**Top Comments:**

> **u/consolationgoal** (5 pts): It looks like you are using straight probabilities from the bookmaker's odds, meaning that the equation is 1/odds = probability. Right?

That means your probabilities include the bookmaker's margin, which in turn shows the expected net to win as zero. In reality, given bookmaker margins, the expected net to win should start out as negative. After all, that's how they make their money. Only by adjusting the probabilities should you be able to move the expected profit to zero or positive. 

In the Leicester City - Man City example, Pinnacle odds are 10.09 x 6.20 x 1.30. That means the bookmaker margin is 2.9% 

(1/10.09) + (1/6.20) + (1/1.30) = 1.029

So unless a person moves the sliders, it the net expected profit from a 10 euro bet should be -0.29 right?
>
> **u/_rbp_** (3 pts): I think there are a few good arguments against parlays:

1. As good as you might be at predicting events, you can't always get everything right. Losing parlays happens often, as the probability of winning decreases exponentially. For example let's say you place 5 bets, each one with a 90% chance winning (as sure as you can be of an outcome in most cases). The chance of winning a parlay is only 90%\^5 = 59%.
2. Parlays are bets with large odds, but a small probability of a payout. Such types of bets drastically increase the variance of your winnings. In other words, you have a larger chance of winning big, but also a larger chance of loosing big. I actually have a nice simulation of that in my [article on variance](https://www.rationalbets.com/articles/#variance).
3. There's one argument I don't think is necessary true, but probably is very often true - when placing a bet, you are paying the bookmaker his margin. The more bets you place in a parlay, the more this margin will increase (as it multiplies across all your picks).

These arguments aren't just theory - I don't believe any professional bettor would do parlays for the above reasons (unless from time to time for fun).
>
> **u/consolationgoal** (3 pts): Thanks for the explanation. You should check out the below paper, which gives great detail on how best to remove the bookmaker margin (including formulas). As you said, there is no exact certainty on how a given bookmaker does it, but the testing in the below paper makes clear the best option for the public to try to remove the bookmaker margin.

[https://www.football-data.co.uk/The\_Wisdom\_of\_the\_Crowd\_updated.pdf](https://www.football-data.co.uk/The_Wisdom_of_the_Crowd_updated.pdf)

I totally understand the desire to maybe not go crazy on precision, but professional sports bettors are often surviving on 1% edges (especially in the major sports like you've got on this tool), so I think precision is key.

More broadly, who is the target market for the tool? I feel like recreational bettors are unlikely to have a probability (even a reasonable range, frankly) for their desired bet, so they might not be able to take advantage of the tool. They are likely going to just line-shop, which your tool does help with but there are other more established options out there for that (Betstamp, etc). 

Originators - i.e. handicappers who create their own probabilities for an event - will be able to fairly easily determine their projected edge.

I don't really do parlays so I didn't check out that part of things, but it's true those probabilities are less well understood generally so that might be something that draws people's attention.

Looks like a lot of work went into the tool. Great job getting to this place.
>
> **u/Available_Remove452** (3 pts): I'm interested in trying this, thank you.
>
> **u/Loyalty4life187** (2 pts): How bout the guys on the book or the tube that wants to tell you how ya become a millionaire 🤣 and they ain’t even one..
>
> **u/_rbp_** (2 pts): I never really analysed picks, but my intuition is in most cases it might be the same as with "investment gurus" selling books - for most it goes, if they were really that good at predicting what will happen, they would simply be making money this way and not seeking a fee for sharing their wisdom.
>
> **u/Loyalty4life187** (2 pts): Sites because this year or maybe I’ve never noticed cause I never paid it no mind just used my own intuition is that what the experts tell people to pick I found that I’m not good at math but say for example SportsLine other night shot every pick wrong.  I mean right now it’s something to do ya know so I been doing basketball n football
>
> **u/Loyalty4life187** (2 pts): Yea I’m lost wish I knew what the heck was talking bout, I do parlays a lot n be off by like 1 game n what not.
>
> **u/_rbp_** (2 pts): Thank you! I hope for some feedback. The concept makes sense to me and works on my devices, and I hope to confirm it does for others too.
>
> **u/Loyalty4life187** (1 pts): I clicked on article what part/ NeverMind I got it
>

---

### [Tennis Analysis #2: Upset Victories](https://reddit.com/r/algobetting/comments/11v0289/tennis_analysis_2_upset_victories/)
**Author**: u/quant_boy123 | **Score**: 12 | **Comments**: 1 | **Date**: 2023-03-18

Hello everyone,

It has been a while since I started what was supposed to be a series focused on tennis analysis from a sports betting perspective. In my first [post](https://www.reddit.com/r/algobetting/comments/ujmpv7/tennis_analysis/), I gave some insights into my motivation and an overview of my data. I also discussed two topics, Implied vs. Realized Probability in tennis betting and O/U Game Lines (theory vs. reality). Moreover, I conducted some backtests based on very simple strategies.

&amp;#x200B;

* Background

My goal for the future is to post more frequently and thereby give you all some trading ideas and valuable insights into tennis analytics. I will typically start with some theory, derived statistics and eventually show some real world betting strategies based on the findings. Whether they would be profitable or not is irrelevant, as both can provide important insights. A bad bet not taken is probably equally valuable as a good bet.

&amp;#x200B;

* Data

For this article, I am only looking at men’s results in official matches for which I have a minimum threshold of data required for the research. My dataset has been growing rapidly recently, since all tournaments have started to resume from the COVID break. Overall, 2022 saw a similar amount of matches as 2016-2019 did (roughly 30000 with clean data) and 2023 is on track to match that. It is important to note that both the quality and quantity of data increased steadily, with more than 60% of the high quality data coming from years &gt;2015.

&amp;#x200B;

* Surprising Outcomes

Today I want to look at upset victories/wins. My definition of an upset is based on bookmaker odds, not on ranking or any other statistics. Bookmaker odds reflect the best guess for the outcome of a match in an efficient market, since they not only take into account the ranking of the two players or their form, but also factors such as the surface, head to head outcomes between the two players and more. Therefore, an upset win can be defined as a win of a player with odds greater than a threshold, let’s say 3 (= Implied Probability roughly 30%, adjusted for vig). 

Firstly, I filter the data to only include players with at least 20 completed matches. Secondly, I exclude players with less than 5 upset wins. Then I start with looking at upset wins with a threshold odd of 3, so every win of a player with odds &gt;3 qualifies as upset win. Since surprises tend to scale with matches played, I rank the outcome by the percentage of upset wins to total matches the player entered as an underdog with odds &gt;3.

Most players making the top 50 of that statistics are ‘newer’ players. This has to do with the fact that most of the high quality data is from recent years, as explained in the Data section. Thus, upset wins from players like Novak Djokovic or Roger Federer are very unlikely, since the data is mainly from a time when they were entering almost every match as a favorite and if they were an underdog, it was typically not with odds &gt;3. 

It is straightforward to see that upset victories typically come at the early stages of the career of a tennis player. That is, when the bookmakers do not have enough information about a players skill. Once they have made some surprising wins, bookmakers lower the odds of the player in subsequent matches to reflect the updated information about their skill level more accurately. Their next wins may therefore not qualify as upset wins anymore, since the odds can be significantly lower than the threshold. This becomes obvious when looking at the odds history of a player like Carlos Alcaraz.

[Graph 1: Carlos Alcaraz ranking vs rolling median odds with a window length of 25 matches.](https://preview.redd.it/k4ugps6iyjoa1.png?width=432&amp;format=png&amp;auto=webp&amp;v=enabled&amp;s=ad92a53e46c91a5f801f8693b075dde24a266b77)

In this graph, the median odds with a rolling window of 25 matches are used. This has the advantage that the curve is smooth and a trend can be easily spotted. Median odds are used instead of average, since the average can plateau on a high level due to one match against a top opponent, for instance Nadal in the French Opens, with very high odds.

In his early days in 2019, when he was first competing in challengers and mainly futures, he often was the underdog. After quick initial success, however, he mainly entered futures tournament matches as the favorite. The same happened in challenger matches in 2020, when he dominated almost every tournament he entered. In 2021, he shifted focus to main tour events, where he often was the underdog. This is where his median odds increase again. In 2022 he had some great victories in the main tour, thus his odds decreased and are now among the lowest of all players, making him the favorite in almost any matchup.

In the following graph, we follow a simple strategy: bet 1 unit on Alcaraz whenever the odds are &gt;3. Obviously, this is with a good portion of hindsight and not a f

[... truncated, see original post ...]

**Top Comments:**

> **u/zahaha** (1 pts): As someone who just got into modeling Woman's Tennis, these are amazing. Please keep it up!

You ever look at live betting trends? Im sure its very hard to get the historical live lines but im curious if there are any situations when "if the pre match odds are &gt;-200 and the live line gets to +300, always take it", or stuff like that.
>

---

### [My AFL Betting Model](https://reddit.com/r/algobetting/comments/11fwf0f/my_afl_betting_model/)
**Author**: u/TheModel_ | **Score**: 12 | **Comments**: 7 | **Date**: 2023-03-02

Hi guys,

Back in lockdown of 2020, I begun developing a model that would pick the result of AFL games, with the ability to use past results of picks to determine the likelihood of future outcomes.

To give context to the success of this system, the last two seasons have netted the following results on selected tips:

2021: 45-24 record, +17.28 units profit, 25.04% ROI

2022: 51-21 record, +26.50 units profit, 36.81% ROI

This season I will be sharing this success, posting tips in the lead up to each round. These tips will be given as bets against the spread, straight up, and on the total.

With the pre-season games set to wrap up this weekend, Round 1 picks will be posted soon - let’s get ready to butcher the bookies!

**Top Comments:**

> **u/BeigePerson** (5 pts): My gut says this is over-fitting and natural variance. 20% ROI is massive. Good luck to you. To avoid criticism I suggest you post bets along with timestamped prices at as reputable book as you can use.
>
> **u/TheModel_** (5 pts): I will be posting all tips weekly, so I encourage you all to jump on board as we make some $$$

I will also be posting tips on Twitter (@TheModelAFL) and Facebook (The Model), so feel free to follow those for more visibility
>
> **u/StatsAnalyticsSports** (3 pts): That's an extremely small sample size. I've had systems be profitable in other sports that were profitable for 6 seasons straight, then completely tanked the 7th &amp; 8th seasons. In addition to having backlogged 6 seasons, going into the 7th season I had well over 600 samples. Good luck
>
> **u/TheModel_** (2 pts): Absolutely mate no issues at all, feel free to comment on Facebook Twitter as well to gain your own following!

I will post the picks in advance of the game, and when doing so will give the confidence %, and a sample size.
>
> **u/tfforums** (2 pts): In the interest of sharing, do you mind if i'm a regular commenter on these posts posting my AFL sheet analysis as well? Also - is this just winning picks or percentage of confidence / chances as well? the latter is very important for EV calculations
>
> **u/PaleontologistThin41** (1 pts): Are you going to be doing the same this year?
>
> **u/outthemirror** (1 pts): I’m most curious your data source. Did you collect data your self or there are data vendors?
>

---

### [Hi, I'm the founder of Sporttrade, a sports betting exchange in New Jersey.](https://reddit.com/r/algobetting/comments/10pn1ri/hi_im_the_founder_of_sporttrade_a_sports_betting/)
**Author**: u/sporttrade | **Score**: 11 | **Comments**: 29 | **Date**: 2023-01-31

Hi reddit,

My name is Alex Kane, and I'm the founder and ceo of Sporttrade.

Before you read this, yes, this is an ad. But it's not one where we hope to earn a bunch of downloads. Instead, my hope is to connect with some of you directly about our product and how you can use it to your advantage.

**A bit about me**

I started Sporttrade in 2018, before sports betting was legal in New Jersey. I didn't really know much about betting at the time. My goal was to create an app that combined betting and trading.

Sometime in 2019, I figured I would try placing a bet. I had followed Captain Jack on twitter, and he had mentioned something about bonus arbitrage. At that time, there were 15 sportsbooks in NJ, all offering $250+ for new players. So, I paired up with my buddy, a math teacher, and set out to NJ to try and take advantage of the bonuses.

Several trips to new States and a few overdrafts of my checking account later, I felt like I had done well to take advantage of various offers, VIP programs, and learned a lot about the industry.

While the perils of online casino ultimately cost me a few thousand 🙄 , I still came out on top, with my profits topping my Sporttrade salary some years! (Pikkit record attached)

**Arbing signup bonuses**

As many of you know, there's a significant profit opportunity presented by the numerous sign-up offers at books like DK and FD.

In short, it looks like this:

Draftkings offers a $1,000 risk free first bet. If the bet loses, you get a $1,000 bet credit back. So, you place a bet on something like "Giants Moneyline" at 3/1 odds on DK, and then "Eagles Moneyline" at 1/3 odds on Fanduel.

Either way, you win/lose $0, but if the Giants lose, DK gives you a $1000 bet credit. You then place another bet "pair" ($1000 bet credit on DK, and an offsetting bet on Pointsbet) to turn that $1,000 credit into cash.

...then onto the next welcome offer.

**What is Sporttrade?**

As I learned more arb betting, I began to realize how beneficial a betting exchange could be to arbitrage bettors. In fact, some of our biggest customers are doing just that; arbing prices and offers of other venues.

Here are some qualities about Sporttrade that make it a must-have for arbers:

➡️ Really tight pricing (as good as -103/-103 on a 50/50 bet)➡️ Transparent limits, and great liquidity (several thousand $ available)➡️ No delays, and instant re-bets

**My offer to you:**

In talking to many of our customers, I realize that while most folks have taken advantage of DK, FD, MGM, PointsBet, CZR offers, they haven't done the same for Betway, WynnBet, Superbook, etc.

So, if any of you are up for it, I'd be more than happy to set up time to meet, introduce you to Sporttrade, and help you use us to get the most out of your betting, whether you're an arbing beginner, or looking to take your game to the next level. My number is below.

Your first bet on Sporttrade is risk free, up to $300 (so I can help you arb that!), and thanks to our partnership with Unabated and OddsJam, you can get access to those tools at a significant discount.

Thanks for reading, and looking forward to connecting with some of you!

Alex(484) 678-8791

**Edit:** You can download the app here:   
https://apps.apple.com/us/app/sporttrade/id1525381125

&amp;#x200B;

[2021 Pikkit Record \(my last year of arbing\)](https://preview.redd.it/j6gn58gzsafa1.jpg?width=1242&amp;format=pjpg&amp;auto=webp&amp;v=enabled&amp;s=795a6562baf0183c81e9825f8921e0739339050b)

**Top Comments:**

> **u/Ok-Seaworthiness3874** (2 pts): Cool idea, and looks like great execution (sorry I'm not in NJ so I can't check), but do you offer e-sports betting? It is VERY difficult to find US based books (Maybe not any tbh, some have only like Super S tier events only) that offer comprehensive offerings of e-sports (it's basically just bovada which is very grey-market, but legit, and thank god for them). 

Considering the MASSIVE growth in e-sports, and especially appealing to a young demographic that probably isn't into traditional sports typically - would you consider adding it?

I'm a bit of a Dota 2 sharp (game with yearly 40M prize pools for players, shit aint no joke) and am on my probably 10th bovada account. Thinking about moving states because the lack of opportunity to bet is frustrating.
>
> **u/SOGorman35** (2 pts): 1) not really a question but I hate you because I had an idea for an exchange like SportTrade (before I knew anything about sports betting) only to discover that it already existed.  I'm definitely rooting for you to succeed.
2) Ohio anytime soon?
3) I know you have said that there are multiple marker makers lined up, and I wouldn't expect you to necessarily identify them, but are any of the MMs affiliated with SportTrade?  I know that Nadex and Kalshi both have affiliates or subsidiaries that function as the primary MMs in their exchanges, so I'm half assuming this is the case here.
>
> **u/afk_again** (2 pts): This looks interesting.  Are there plans to support horse racing?  Also can you post again when there's API access.  A swagger page would be nice too.
>
> **u/Fly-iggles-fly** (1 pts): Is Spanky one of your market makers?
>
> **u/Artistic_Dog_** (1 pts): Hey Alex, how is this developing? Do you have a trading API or connection to trading software like Bet Angel or GeeksToy? Super interested on this
>
> **u/sporttrade** (1 pts): Now in NJ/CO/IA/AZ/VA, we’d like to launch in:

IN/MD/KY/NC/MI/IL/PA/OH/MO/WV/LA/MA/KS

although some of those states will require some legislative changes
>
> **u/madtadder** (1 pts): I reached out to them directly in February, and they said "We haven’t made available our pricing api to individuals just yet. Once we do that, we fear the floodgates will open and we would need to rebuild our market data endpoint service to handle the load" which is sorta hilarious since they claim to have an API that's available
>
> **u/random-50** (1 pts): Any trading api yet, or imminent?

What’s the pipeline of states?
>
> **u/poubelleaccount** (1 pts): I don't see much liquidity on [https://markets.getsporttrade.com/nj](https://markets.getsporttrade.com/nj); for instance, there doesn't seem to be a market on the Pacers game today. Is that a bug?
>
> **u/OliverAlden** (1 pts): Thanks.  Just discovered sports trade which is new to my state.
>

---

### [Making NBA models](https://reddit.com/r/algobetting/comments/1e0ptxd/making_nba_models/)
**Author**: u/makingstuff237 | **Score**: 9 | **Comments**: 16 | **Date**: 2024-07-11

Hi everyone, I've downloaded every box score, quarter box score and even play by plays for every nba game and then I scraped all of the info into an sql database. I've made a few VERY basic models and would like ideas on what to do next.

My most advanced model (still super basic) takes two teams and a date (usually automated by the days schedule so it does it automatically) and spits out predicted stats for each player. I get the prediction by taking a look at stats over the past 5, 10, 20 games as well as full season, but I only look at the home or road games depending on the team. So if it's BOS at LAL I would look at Boston's past 5, 10, 20 and any game played on the road and vice versa for LA. For each of those splits (5, 10, 20, all) I get the players average stats, the opposing teams average defensive stats and the nba average defensive stats for those spans for each quarter, 1-4. I then compare the nba average defensive stats (on the road or at home, to match the team I'm looking at) to the teams defensive stats and make it a percentage. So let's say NBA average on the road allows 10 fg3a's in the first quarter but let's say Boston allows 9.5 fg3a's in the first over the same split, then my algorithm would have Boston's fg3a percentage at 95%, then I take the players averages and multiply it by the percentage to get my estimate. I do this for every stat I can. 

The program then looks at the odds which I scrape from draft kings and then compares the bet to my predicted stat and gives a confidence rating which is not impressive, it's literally just comparing my prediction to the line and then giving a bonus multilier depending on it's value, so if I show a player having 9 rebounds and the line is set at 7.5 and the over is -140 then I have a difference of 120% and then I multiply that by how far away the value is from 0, the further negative the lower the multiplier. I don't 100% remember how I did this and can't look it up on this computer right now but suffice to say it's very lacking. I have it spit out the bets it thinks are best and usually it picks about 5-10 bets per day, of those it had a pretty high ROI but the model is so simple and it needs improvement. It has obvious flaws like not being able to know who is and who isn't playing in a game among I'm sure 10,000,000 other things.


This was started as just a fun project to teach me how to scrape websites and use mysql but I'd like to learn more. I don't know about betting strategies or EV betting or anything really, I'm just 100% self taught. Any advice on what to look into would be great. Also worth noting I've only utilized full game and quarter box score information, I have not done anything with my play by play table. I've also written some code so it can identify who is on the court at any time and shows all 10 players on the court for any play and combined it with the shots data available to get the x and y coordinates of any shot taken. Here's a screenshot of my altered pbp table: https://imgur.com/a/4BxHCXW (note that it cuts off and doesn't show all 10 players in the screen shot, they're all in the table, they just didn't all fit in the screenshot.

I also have a players table with everyone's names, hand, height, weight, dob, draft info, college info, etc. As mentioned, this started out as a project to teach me python and mysql.

Everything is sourced from basketball reference and draft kings, 100% free, if anyone would be willing to help me I might be willing to share my scraping scripts.

**Top Comments:**

> **u/LawyersGunsMoneyy** (3 pts): My thought process is that the implied odds based on the line is what you need to hit to be profitable. So if there’s a line that is listed at +100, you need to hit 50% to break even, regardless of whether the line has 1% juice or 20% juice
>
> **u/makingstuff237** (2 pts): Thank you so much for the tip, I'll check it out!
>
> **u/kicker3192** (2 pts): Yes, this. De-vigging the lines only serves if you're going to utilize the books' implied probability to calculate something within the model (i.e. your model is top down and you're going to use the books' odds as a variable).
>
> **u/ezgame6** (2 pts): you still bet on the vigged odds... what you're saying is if you want to estimate your true edge? I don't see how vig free odds affect your decision making
>
> **u/makingstuff237** (1 pts): Kind of. It was a ton of work and I'm not willing to share it for free. Nor do I have a place to host it
>
> **u/fuckosta** (1 pts): Hey would you mind if I could have a look at your dataset?
>
> **u/Foreign-Procedure-91** (1 pts): Hello. Apparently it's a very interesting job.
    Does your model take into account how the absence of a player affects other players?
    For example, if a player is absent, and his individual contribution will change little. But this could have a greater impact on the game of other players
>
> **u/NarwhalDesigner3755** (1 pts): NBA API doesn't have everything, I had to merge their data with another source that I had scraped to give me a more complete picture
>
> **u/Traditional_Soil5753** (1 pts): From my experience if you use the Kelly criterion formula you don't have to worry about "de-vigging". Sports books odds can also be viewed as "% of wager returned"...ie +200 odds is just 100% of your wager returned on a win. +300 odds is just 200% of wager returned....plug this into Kelly criterion formula for your bet size and your good to go....
>
> **u/DotSlashSports** (1 pts): No problem. I'd listen to some of the Spotify podcasts with the person who did DARKO. His name is Kosta. I'm sure you will get some good nuggets of info from them.
>

---

### [MMA AI &amp; Project Sharing](https://reddit.com/r/algobetting/comments/jzhyqk/mma_ai_project_sharing/)
**Author**: u/akkatips | **Score**: 9 | **Comments**: 3 | **Date**: 2020-11-23

Recently, we've created an MMA AI which predicts the outcome of UFC fights. There are numerous variables used ranging from each fighter's reach to the number of KO wins they've had in the UFC to the number of strikes they threw last fight. All these variables are inputted into the AI each week and as a result generates predictions. 

The backtesting of the AI gave us some very promising results (Since Jan 2019):

**Total Profit: +49.63U** 

**Average Profit per Event: +0.64U**  

**Average ROI: +8.67%** 

**Here are the graphs showing this in a more visual format:** [**https://imgur.com/a/Fdu0oSq**](https://imgur.com/a/Fdu0oSq)

We have also been working on an extra MMA AI that aims to predict whether a fight will go the distance or not. Last weekend we were able to combine the predictions from both AIs to predict a 6.50 odds winner at the weekend, we even pre-posted it on Reddit!

Has anyone else been working on some interesting projects and found profitable strategies as a result?

**Top Comments:**

> **u/bluelotus214** (1 pts): Wicked.  I'm looking for some data on this.
>
> **u/RepresentativeDig921** (1 pts): Strategy.

Bet every single MMA dog like this

Win

By TKO, KO

By Submission

Profit.
>
> **u/plinifan999** (1 pts): Hello! Several questions:

\--How do you get your data?

\--What type of model are you using?
>

---

### [Best Algorithmic Market Making Strategy?](https://reddit.com/r/algobetting/comments/1ieed8t/best_algorithmic_market_making_strategy/)
**Author**: u/nvng | **Score**: 7 | **Comments**: 9 | **Date**: 2025-01-31

Most of the content I see on this sub is about building a profitable model to predict the outcome of a match, but whats the best way to make money once we have a good model? Seems that most people are just doing straight EV bets but MM strategies on exchanges sound way more attractive. No limiting/banning, often can bet higher volumes, and some of these exchanges even offer rebates for high volume. 

So what goes into these algorithmic market making strategies? Is it just simple mispricing, i.e. you find a theoretical value and quote the market at a profitable margin? Or is it more complex where people are building advanced hedges and grouping bets to create spreads.

**Top Comments:**

> **u/BetBrotherApp** (1 pts): As a rule of thumb bookmakers always have the most accurate models plus an edge. 

Try to compare prices across a range of bookmakers and look for differences. The research paper “Beating the bookies with their own numbers - and how the online sports betting market is rigged” is a decent paper on this. 

Line movements is incredibly important, as well as placing bets early enough before the odds drop

Lastly looking at psychological factors plays a role, often times markets are mispriced due to overall sentiment not actual data
>
> **u/neverfucks** (1 pts): if you put up a sign that says "i'm willing to sell eagles +1.5 at -105 and buy eagles +1.5 at +105" you are not only a market maker, you're a sportsbook operator and you need a license unless you are doing your market making on an exchange like novig that is legal in your state.
>
> **u/redtwinned** (1 pts): Huh, didnt know you could do that. I live in a state where books aren’t legal but fantasy apps are, so I’m on a friend’s book. Normally he has me generate lines for local games that aren’t offered by his website that he uses. Maybe I should talk to the backers about getting a deal lmao
>
> **u/BowTiedBettor** (1 pts): and some of these exchanges charge hefty fees on profits
>
> **u/neverfucks** (1 pts): market making. you put up a sign that says "i'm willing to buy up to 50 apples from anyone for a dollar and i'm willing to sell up to 50 apples for a dollar 5" and bam you are making a market in apples. if you sell as many apples as you buy, you've done well as a middleman and you make a profit. if people are much more interested in either buying from you or selling to you, you need to move your prices or you will get trucked. welcome to capitalism baby
>
> **u/grammerknewzi** (1 pts): What difference is there between market making and showing two sided lines like a book does? Both are accepting two sided risk for enough edge.
>
> **u/jbet13** (1 pts): It’s called market making, also not necessarily looking for equal volume
>
> **u/ZeltronTheHellspawn** (1 pts): https://preview.redd.it/vrq40qkpcfge1.jpeg?width=250&amp;format=pjpg&amp;auto=webp&amp;s=79a55c13c2e4b775f43bfc3a21ce82dd1a10a20e
>
> **u/grammerknewzi** (1 pts): pretty sure this is just called being a book; your really just scalping odds by hoping you get large, but equal volume on both sides of a spread for example.
>
> **u/jbet13** (1 pts): Don’t think anyone will give away the secrets of this one but just remember 
- adverse selection 
- nice prior price 
- move with money 
- know where high variance price moves may occur
>

---

### [Types of stat/cs college classes for better intuition and knowledge for sports modeling?](https://reddit.com/r/algobetting/comments/1fnnvho/types_of_statcs_college_classes_for_better/)
**Author**: u/GeometricBison9 | **Score**: 5 | **Comments**: 7 | **Date**: 2024-09-23

Hello, I am a college student studying essentially a dual degree in CS and Stats. I’ve been betting for 7 months through a discord and have an 18% ROI on pikkit. I am very interested in trying to beat the books using my own data analysis and modeling. For those who have this background, what types of classes are important for this type of work? I know a huge part of finding edges is analyzing Sportsbooks odds and EV, but I was wondering what type of statistical stuff is good to take?
I have pretty solid CS knowledge and can learn stuff pretty quickly, and I already have done quite a bit of web scraping, web dev, and basic ML with scikit and PyTorch.

My repertoire: stat modeling, lin alg, calc3, stats and prob, stochastic processes, data structures, artificial intelligence

Any advice is greatly appreciated!

**Top Comments:**

> **u/__sharpsresearch__** (11 pts): The biggest hurdle i see everyone here with is the fact that ~~no one can~~ most people cannot program properly. You will be able to move faster and learn more than anyone if you can understand how to create a psql database and stand up a server on digital ocean.

programming is 95% of the work to be good at algobetting. Most "AI" in algobetting is best done with xgboost, logistic or linear regression so know these really well, calc/advanced datastructures are borderline useless.

Learn as much about feature engineering as you can.
>
> **u/jbr2811** (4 pts): To piggy back off of this, scraping lines and stats and managing a database of all that info is a huge part of it. Focus on programming first of your intention is to originate your own numbers.
>
> **u/Shallllow** (2 pts): It's not a be-all end-all, just more flexible. I'd wager the best DL people are better than the best LGBM/XGBoost people, but the median case is better for boosting. Not sure what your point is with the latter, some other kind of model?
>
> **u/fysmoe1121** (2 pts): and not getting IP banned for web scraping off sites you’re not suppose to lol
>
> **u/Mr_2Sharp** (1 pts): Strangely enough feature engineering wasn't taught in any of my classes but it's basically the most important part imo. You can have chatgpt get you 80% through to running a model in Python the rest will take you anywhere from 20 minutes to an hour depending on your experience. Feature engineering on the other hand is an entirely different beast and can take enormous amounts of time from gathering, organizing, and cleaning data to having the mathematical maturity and insight to create your own features. This is expedited by having programming skills as others here have said. So definitely learn to feature engineer in some programming language. As to which language is optimal is anybody's guess.
>
> **u/KolvictusBOT** (1 pts): Doubtful deep learning is the be-all end-all answer. I did not mention deep learning on purpose. But you can go beyond dumping csvs into xgboost. And in the future, I highly doubt that that(xgboost) will in any way provide you an edge over the market as a small-time operation without data that others lack.
>
> **u/Shallllow** (1 pts): Models can only be as complex as the amount of data you have, high frequency trading? Sure, deep learning is gonna be on top. Betting on 10s or 100s of games? Having a solid understanding of fundamental stats, good prior assumptions, and quality data is much more important.
>

---

### [From Simple Models to Market Analysis: Is It Even Worth It?](https://reddit.com/r/algobetting/comments/1i7c0ma/from_simple_models_to_market_analysis_is_it_even/)
**Author**: u/National-Yogurt7021 | **Score**: 4 | **Comments**: 5 | **Date**: 2025-01-22

Some time ago, I started collecting historical data from football leagues and built a simple Python script. The script searches for teams in future matches based on specific criteria and finds teams with similar characteristics in the historical data. From a larger sample of the identified matches, it derives win probabilities and odds. I initially tested it with just one criterion, namely the average points per game. In the backtest, this resulted in a -12% yield, which didn’t surprise me, as it was extremely rudimentary. In that sense, it was amusingly a good contrarian indicator, so I tested a betting strategy based purely on randomness in the backtest. Even that performed better with a yield of -8%, lol.

I then planned to implement additional metrics to refine the model but decided instead to test the model provided by the site [xgscore.io](http://xgscore.io) by creating a Blogabet account. The reason was that I thought the approach used by the site seemed very sophisticated, and I probably wouldn’t be able to do better. On Blogabet, after 416 bets using their odds, I am currently at a yield of -7%. The sample size isn’t that large yet, but I find it hard to believe that it will improve significantly over time. The average odds are 2.318 (43%), with a win rate of 42%.

As of now, this would imply that the market odds (all bets placed on Pinnacle) pretty much reflect the actual win probabilities. This raises the question of whether it’s even worth pursuing such a project further, given how efficient the market seems to be. Respect to everyone who has managed to build a profitable model in these markets.

---

### [NBA player prop stats scraping](https://reddit.com/r/algobetting/comments/13w2no6/nba_player_prop_stats_scraping/)
**Author**: u/fiachrah98 | **Score**: 4 | **Comments**: 4 | **Date**: 2023-05-30

Hi,
I’ve been running a player prop betting system for NBA since start of conference finals but it consists of me going to different websites and copying and pasting info every day.

These are the website I need a way of extracting the table from into a google sheet.

Any help is appreciated.

https://www.nba.com/stats/players/traditional?PerMode=Totals&amp;LastNGames=5

https://www.lineups.com/nba/nba-player-minutes-per-game

System after conference finals:

Bets: 121
Profit: 22.71u
ROI: 14.6%

---

### [Feature Engineering CFB Win-prediction Model](https://reddit.com/r/algobetting/comments/1g4djdx/feature_engineering_cfb_winprediction_model/)
**Author**: u/Durloctus | **Score**: 4 | **Comments**: 0 | **Date**: 2024-10-15

Anyone wanna talk predictors for CFB models?

I have a model I’ve had some success with last season and this season (so far) and I feel good about the features I’m using (ypg, off and def success rates, first downs per game, and an engineered feature that gives a ‘grade’ for game per the score margin and strength of opponent) but wondering what some of you feel are the best predictors for winners of games.

My goal a is give a &gt;= 5% return on money bet (moneyline only) for the cfb season, weeks 6-13. Last season saw a 14.83% return and this season is at 8% through two weeks.

---

### [Beating books on NBA Props](https://reddit.com/r/algobetting/comments/1kf2o9j/beating_books_on_nba_props/)
**Author**: u/Consistent_Buy625 | **Score**: 3 | **Comments**: 1 | **Date**: 2025-05-05

I’ve been testing a few different models against NBA player props (points, assist, rebounds) to see how they compare to sportsbooks. I’ve been using things like the way back machine on rotowire to obtain large amounts of previous props at once. I’m wondering if it’s worth also testing across playoff seasons to see if there is any variance due to playoff performance from players being different than the regular season, and also how much of an edge I would need in order to break even/become profitable

---

### [What sample size is significant?](https://reddit.com/r/algobetting/comments/18oltok/what_sample_size_is_significant/)
**Author**: u/verrts_ | **Score**: 3 | **Comments**: 9 | **Date**: 2023-12-22

I was doing backtests on +600 games. Although there is no look-ahead bias in my backtest, the results look a bit too good to be true:

* Sharpe ratio: 3.12
* Win rate: 46.5%
* Average ROI per won bet: 152% (edit for clarification: On average for every $1 won bet I get $2.52 in total. $1.52 is the profit).
* Risking 5% of the account balance per bet (initial balance: $1000) would yield at the end $55,000
* Biggest losing streak: 7
* Biggest drawdown: 36%

What do you think? Is it realistic? Is my sample size good enough to rely on this backtest?

---

### [Underdog NFL +EV Record by Week](https://reddit.com/r/algobetting/comments/1iolda6/underdog_nfl_ev_record_by_week/)
**Author**: u/FavoredProps | **Score**: 2 | **Comments**: 0 | **Date**: 2025-02-13

**What’s up! We graphed the hit rate for props identified as +EV on the Underdog DFS site for the 2024 NFL Regular Season.** 



**Approach:**

⁃    Included standard-payout props with -125 or better average odds from 4+ sportsbooks

⁃    Props with line changes were considered separate props

⁃    Since we had 15 minute snapshots of data, the last occurrence of a prop was used to prevent duplicates



The **overall hit rate for the regular season was 54.6%** over 3601 props that were included in the approach above. For context, the **breakeven hit rate for each pick in a 6-leg flex parlay is 53.8%.** 



**Also, “Under” +EV props are more accurate and made up just 40% of the total count.**

⁃    Over: 53.9%

⁃    Under: 55.7%



It seems like blindly tailing +EV plays this season would’ve earned a small profit. To help get those numbers up, we made a Free Player Prop Tool [https://www.favoredprops.com/dfs/nba](https://www.favoredprops.com/dfs/nba) to research more data points like defensive rankings, line movement, and hit-rate in various situations



**Let us know if you’d like to see more content like this!**

https://preview.redd.it/553omucibxie1.jpg?width=1440&amp;format=pjpg&amp;auto=webp&amp;s=858e96555ef6bd79da1384c5d62ee3dc61b38483

---

### [Technical analysis on sports](https://reddit.com/r/algobetting/comments/1k0euwc/technical_analysis_on_sports/)
**Author**: u/Zestyclose-Gur-655 | **Score**: 2 | **Comments**: 0 | **Date**: 2025-04-16

On the stock market technical analysis of charts is very popular. 

Usually bookmakers don't offer any charts at all. (But they don't even want people to win, they barely show you profit and loss because they rather hide people are losing.)  
Some betting exchanges have charts, betinasia also does. 

Does it make sense to use any charts for betting and why not? 

Maybe i'm crazy but i found if i analyse a game, sometimes it's quite obvious where the money is coming in on. Because bookies just keep moving the price on one side. You can basically see it on the chart where people have been betting on. It kind of tells the story of that particular market.

In theory if you have a chart where the odds are constantly dropping, you first back at a good price then later lay it. This creates some value. Or vice versa with odds that are becoming bigger, so less of a % chance. First lay it then back it. 

The problem is maybe events that are going one side don't have to keep going that side. I think it does slightly more often then not but this is just an assumption that i make, i don't have hard data on if steamers more often then not keep steaming. 

I'm just trying to think like a bookie right now, essentially they just back and lay bets with a spread in between. This is similar to market makers, actually it is a form of market making. The real value then to me seems to anticipate where odds are going to, more so then where they are now. This is also true for gamblers, and even gamblers are just trying to beat closing line value, get a better value themselves. This indicates a profitable strategy. So if odds move in your advantage more often then not, this is part of the goal to me it seems. 

Say you was a bookmaker, in essence the best thing for them is have some markets that just go sideways forever with a big spread. They can constantly buy and sell, buy and sell and make a profit. Often you do see that odds move a certain direction. For bookmakers this is somewhat of a loss because their odds where first not correct. This is also why you can only bet little when an event is days away and big when it nears to start. The price has to shape to where it should be. Once everyone made their bets they know pretty good where it should about be priced. 

Maybe i spend too much time on the stock market but i do see also just trends, mean reversions, support and resistance in betting markets. In fact i think betting markets are even way more logical then financial markets. There might also be manipulation by single actors but for a bookie it's not good if odds are much different then where the real odds should be. Mispriced events makes it possible to value bet, since only the outcomes in reality influences the outcome of a bet. On financial markets it's mostly just price alone that has any meaning, fundamentals to a lesser extent. Option contracts are based on the price of the underlying not on the outcome of events. So there is much more what George Soros would call: "reflexivity" possible. Even the market participants itself can influence reality.

---

### [Anyone know the status of MySportsFeeds.com?](https://reddit.com/r/algobetting/comments/105q4et/anyone_know_the_status_of_mysportsfeedscom/)
**Author**: u/postrema19 | **Score**: 2 | **Comments**: 4 | **Date**: 2023-01-07

Hi All.  Long time lurker/first time poster.  I have a background as software developer and am very interested in this space, but am finding it difficult locating a good source of historical data and/or feeds.

I  recently stumbled across what looked to be a promising API provider at [MySportsFeeds.com](https://MySportsFeeds.com), but have found them to be unresponsive.   The API and data modeling seem to be pretty mature and well organized, but I recently found that it is not returning data for NCAAM basketball, so I'm beginning to wonder if this site is now defunct.

Does anyone have any insight into the status of this provider?  If not, any recommendations in terms of other providers in this area would be well appreciated.  I am primarily interested in data for the "big four" of the US (NFL, MLB, NBA and NHL) as well as college basketball data.

Any help or direction is greatly appreciated!

---

### [Model Evaluation](https://reddit.com/r/algobetting/comments/1fzzp9e/model_evaluation/)
**Author**: u/usmanirale | **Score**: 1 | **Comments**: 16 | **Date**: 2024-10-09

I am backtesting a model, and after backtesting for seven seasons, I got the following result: I start each season with a 1000-dollar bankroll, using the Kelly criterion and a max stake of 2% of the bankroll. I want to know if this outcome is inline with a winning model.



1. Win Rate:

2024: 60.32%

2023: 75.36%

2022: 42.67%

2021: 37.50%

2019: 50.56%

2018: 55.32%

2017: 52.63%



Average win rate: 53.48%



2. ROI (Return on Investment):

2024: 51.77%

2023: 117.78%

2022: -21.42%

2021: 0.05%

2019: 70.33%

2018: 26.64%

2017: 26.32%



Average ROI: 38.78%



3. Average Value Percentage:

2024: 28.72%

2023: 25.80%

2022: 34.19%

2021: 45.74%

2019: 29.48%

2018: 40.10%

2017: 29.11%



Average value percentage: 33.31%



4. Log Loss (Predictive vs Historical):

2024: 0.4643 vs 0.4765

2023: 0.5018 vs 0.5488

2022: 0.5197 vs 0.4999

2021: 0.4829 vs 0.4896

2019: 0.6484 vs 0.6531

2018: 0.5355 vs 0.5650

2017: 0.5827 vs 0.5828



Average Predictive Log Loss: 0.5336

Average Historical Log Loss: 0.5451



5. Profit/Loss:

2024: +$517.68

2023: +$1,177.78

2022: -$214.17

2021: +$0.54

2019: +$703.31

2018: +$266.43

2017: +$263.24



Total profit over 7 seasons years: $2,714.81

---

## Statistical Models & Methods

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [My AFL Betting Model](https://reddit.com/r/algobetting/comments/11fwf0f/my_afl_betting_model/)
**Author**: u/TheModel_ | **Score**: 12 | **Comments**: 7 | **Date**: 2023-03-02

Hi guys,

Back in lockdown of 2020, I begun developing a model that would pick the result of AFL games, with the ability to use past results of picks to determine the likelihood of future outcomes.

To give context to the success of this system, the last two seasons have netted the following results on selected tips:

2021: 45-24 record, +17.28 units profit, 25.04% ROI

2022: 51-21 record, +26.50 units profit, 36.81% ROI

This season I will be sharing this success, posting tips in the lead up to each round. These tips will be given as bets against the spread, straight up, and on the total.

With the pre-season games set to wrap up this weekend, Round 1 picks will be posted soon - let’s get ready to butcher the bookies!

**Top Comments:**

> **u/BeigePerson** (5 pts): My gut says this is over-fitting and natural variance. 20% ROI is massive. Good luck to you. To avoid criticism I suggest you post bets along with timestamped prices at as reputable book as you can use.
>
> **u/TheModel_** (5 pts): I will be posting all tips weekly, so I encourage you all to jump on board as we make some $$$

I will also be posting tips on Twitter (@TheModelAFL) and Facebook (The Model), so feel free to follow those for more visibility
>
> **u/StatsAnalyticsSports** (3 pts): That's an extremely small sample size. I've had systems be profitable in other sports that were profitable for 6 seasons straight, then completely tanked the 7th &amp; 8th seasons. In addition to having backlogged 6 seasons, going into the 7th season I had well over 600 samples. Good luck
>
> **u/TheModel_** (2 pts): Absolutely mate no issues at all, feel free to comment on Facebook Twitter as well to gain your own following!

I will post the picks in advance of the game, and when doing so will give the confidence %, and a sample size.
>
> **u/tfforums** (2 pts): In the interest of sharing, do you mind if i'm a regular commenter on these posts posting my AFL sheet analysis as well? Also - is this just winning picks or percentage of confidence / chances as well? the latter is very important for EV calculations
>
> **u/PaleontologistThin41** (1 pts): Are you going to be doing the same this year?
>
> **u/outthemirror** (1 pts): I’m most curious your data source. Did you collect data your self or there are data vendors?
>

---

### [Hi, I'm the founder of Sporttrade, a sports betting exchange in New Jersey.](https://reddit.com/r/algobetting/comments/10pn1ri/hi_im_the_founder_of_sporttrade_a_sports_betting/)
**Author**: u/sporttrade | **Score**: 11 | **Comments**: 29 | **Date**: 2023-01-31

Hi reddit,

My name is Alex Kane, and I'm the founder and ceo of Sporttrade.

Before you read this, yes, this is an ad. But it's not one where we hope to earn a bunch of downloads. Instead, my hope is to connect with some of you directly about our product and how you can use it to your advantage.

**A bit about me**

I started Sporttrade in 2018, before sports betting was legal in New Jersey. I didn't really know much about betting at the time. My goal was to create an app that combined betting and trading.

Sometime in 2019, I figured I would try placing a bet. I had followed Captain Jack on twitter, and he had mentioned something about bonus arbitrage. At that time, there were 15 sportsbooks in NJ, all offering $250+ for new players. So, I paired up with my buddy, a math teacher, and set out to NJ to try and take advantage of the bonuses.

Several trips to new States and a few overdrafts of my checking account later, I felt like I had done well to take advantage of various offers, VIP programs, and learned a lot about the industry.

While the perils of online casino ultimately cost me a few thousand 🙄 , I still came out on top, with my profits topping my Sporttrade salary some years! (Pikkit record attached)

**Arbing signup bonuses**

As many of you know, there's a significant profit opportunity presented by the numerous sign-up offers at books like DK and FD.

In short, it looks like this:

Draftkings offers a $1,000 risk free first bet. If the bet loses, you get a $1,000 bet credit back. So, you place a bet on something like "Giants Moneyline" at 3/1 odds on DK, and then "Eagles Moneyline" at 1/3 odds on Fanduel.

Either way, you win/lose $0, but if the Giants lose, DK gives you a $1000 bet credit. You then place another bet "pair" ($1000 bet credit on DK, and an offsetting bet on Pointsbet) to turn that $1,000 credit into cash.

...then onto the next welcome offer.

**What is Sporttrade?**

As I learned more arb betting, I began to realize how beneficial a betting exchange could be to arbitrage bettors. In fact, some of our biggest customers are doing just that; arbing prices and offers of other venues.

Here are some qualities about Sporttrade that make it a must-have for arbers:

➡️ Really tight pricing (as good as -103/-103 on a 50/50 bet)➡️ Transparent limits, and great liquidity (several thousand $ available)➡️ No delays, and instant re-bets

**My offer to you:**

In talking to many of our customers, I realize that while most folks have taken advantage of DK, FD, MGM, PointsBet, CZR offers, they haven't done the same for Betway, WynnBet, Superbook, etc.

So, if any of you are up for it, I'd be more than happy to set up time to meet, introduce you to Sporttrade, and help you use us to get the most out of your betting, whether you're an arbing beginner, or looking to take your game to the next level. My number is below.

Your first bet on Sporttrade is risk free, up to $300 (so I can help you arb that!), and thanks to our partnership with Unabated and OddsJam, you can get access to those tools at a significant discount.

Thanks for reading, and looking forward to connecting with some of you!

Alex(484) 678-8791

**Edit:** You can download the app here:   
https://apps.apple.com/us/app/sporttrade/id1525381125

&amp;#x200B;

[2021 Pikkit Record \(my last year of arbing\)](https://preview.redd.it/j6gn58gzsafa1.jpg?width=1242&amp;format=pjpg&amp;auto=webp&amp;v=enabled&amp;s=795a6562baf0183c81e9825f8921e0739339050b)

**Top Comments:**

> **u/Ok-Seaworthiness3874** (2 pts): Cool idea, and looks like great execution (sorry I'm not in NJ so I can't check), but do you offer e-sports betting? It is VERY difficult to find US based books (Maybe not any tbh, some have only like Super S tier events only) that offer comprehensive offerings of e-sports (it's basically just bovada which is very grey-market, but legit, and thank god for them). 

Considering the MASSIVE growth in e-sports, and especially appealing to a young demographic that probably isn't into traditional sports typically - would you consider adding it?

I'm a bit of a Dota 2 sharp (game with yearly 40M prize pools for players, shit aint no joke) and am on my probably 10th bovada account. Thinking about moving states because the lack of opportunity to bet is frustrating.
>
> **u/SOGorman35** (2 pts): 1) not really a question but I hate you because I had an idea for an exchange like SportTrade (before I knew anything about sports betting) only to discover that it already existed.  I'm definitely rooting for you to succeed.
2) Ohio anytime soon?
3) I know you have said that there are multiple marker makers lined up, and I wouldn't expect you to necessarily identify them, but are any of the MMs affiliated with SportTrade?  I know that Nadex and Kalshi both have affiliates or subsidiaries that function as the primary MMs in their exchanges, so I'm half assuming this is the case here.
>
> **u/afk_again** (2 pts): This looks interesting.  Are there plans to support horse racing?  Also can you post again when there's API access.  A swagger page would be nice too.
>
> **u/Fly-iggles-fly** (1 pts): Is Spanky one of your market makers?
>
> **u/Artistic_Dog_** (1 pts): Hey Alex, how is this developing? Do you have a trading API or connection to trading software like Bet Angel or GeeksToy? Super interested on this
>
> **u/sporttrade** (1 pts): Now in NJ/CO/IA/AZ/VA, we’d like to launch in:

IN/MD/KY/NC/MI/IL/PA/OH/MO/WV/LA/MA/KS

although some of those states will require some legislative changes
>
> **u/madtadder** (1 pts): I reached out to them directly in February, and they said "We haven’t made available our pricing api to individuals just yet. Once we do that, we fear the floodgates will open and we would need to rebuild our market data endpoint service to handle the load" which is sorta hilarious since they claim to have an API that's available
>
> **u/random-50** (1 pts): Any trading api yet, or imminent?

What’s the pipeline of states?
>
> **u/poubelleaccount** (1 pts): I don't see much liquidity on [https://markets.getsporttrade.com/nj](https://markets.getsporttrade.com/nj); for instance, there doesn't seem to be a market on the Pacers game today. Is that a bug?
>
> **u/OliverAlden** (1 pts): Thanks.  Just discovered sports trade which is new to my state.
>

---

### [Soccer Value Betting Team](https://reddit.com/r/algobetting/comments/120mki5/soccer_value_betting_team/)
**Author**: u/AssignmentHelpful | **Score**: 8 | **Comments**: 8 | **Date**: 2023-03-24

Hey pals, I’m looking to build a small team (3-5 people) to develop a system to price the following soccer markets: moneyline, over/unders and Asian handicaps. 

I recognize the difficulty in pricing soccer given the popularity of the sport, the high cost of data and the competition from big betting syndicates, but I believe there are pricing inefficiencies that we can exploit using feature engineering on event data. The development of the infrastructure will most likely take between 5-10 months with the right people. I have already tackled some of the scrapping and data wrangling required, but I’m still far from having a streamlined system.

The project will entail:
- Scrapping and cleaning event data (started)
- Scrapping and cleaning odds data (started)
- xG, xThreat model implementations (started)
- Feature engineering 
- Developing machine learning modes
- Testing accuracy of the models
- Deploying everything to servers/cloud

This should be a fairly big project, so I don’t expect many of you to be interested. 
The worst case scenario is that we don’t find any edge, if that’s the case we would still have the infrastructure to do any other projects regarding soccer. 

Let me know if you are interested or if you are just curious about the project and it intricacies.

PD: I’m coding in python and storing data in SQL

**Top Comments:**

> **u/TheBigLT77** (1 pts): New to algo but ten years betting on soccer and played at a high level. Happy to help
>
> **u/yungreseller** (1 pts): I’d recommend a different sport, if you print the premium free pinnacle odds against the odds implied by results, you usually find that if there are mispricings they are usually covered by the bookies premium. I mean think about it, in this market alpha can only exist for you, if you are the only one knowing it.
>
> **u/AssignmentHelpful** (1 pts): The idea would be to develop models that beat the closing line on sharp bookmakers (pinnacle and betcris), so that you can consistently bet sizeable amounts on these sites without the danger of getting restricted or banned. Way easier said than done, but I’m certain that it’s achievable on some markets.
>
> **u/boardsteak** (1 pts): How do you expect to capitalize on your results?
>

---

### [My attempt at a model to bet on NFL games](https://reddit.com/r/algobetting/comments/ggaz71/my_attempt_at_a_model_to_bet_on_nfl_games/)
**Author**: u/HamirTime | **Score**: 8 | **Comments**: 14 | **Date**: 2020-05-09

Hey guys, been lurking since this subreddit got created and knew I would be contributing to it once I got my model to an "acceptable" state to hopefully get further insight.

Gonna try to keep this as short as possible because alot of explaining happens in the Jupyter notebook, but here goes.

So basically I took a data mining course this last semester and the final project was to apply the concepts we learned in class to a real world scenario. While the NFL was in full swing, I was a frequent sports better and would really enjoy betting and watching the games. Data and modeling still seemed like such a complex topic to me, but I knew that eventually I would the subject either in class or on my own. After learning the data mining world, this in-class project was a perfect way to test what I had learned as well as try and use my skills to make some money.

SO with all that out of the way, the summation of the actual data and models is that I took game data from Kaggle (mainly used to pull the scores) and added full team rosters for both away and home teams (rosters scraped from another site). My thought was that since each team is composed of 52 players, that at the end of the day their performances (with the leadership of the head coach) is what determined the outcomes of the game. So to summarize, each of my records contained the home and away teams, current W-L records, and most relevant positions for both teams. I also decided to filter the data to only be within this millennia.

With this data I tried to use regression models to predict the score of the games. This score would then be compared with the vegas spread for that game so that the model could predict whether it should bet on the home team or the away team to cover the spread. This might not be a good practice, but I just decided to use every game from the 2000-2018 season to predict 2019 games as my model testing phase. I used the SVM Regressor algorithm (primarily because it was the only one that supported unbalanced data, which is obviously important since the more recent games should play a bigger factor) and an Artificial Neural Network because it's pretty easy to grasp and honestly doesn't require much thinking or work from me. Kinda also used it in case I was configuring the SVM wrong.

In summary, my results were slightly worse than I was expecting.  Both my models average out to about 52% accuracy and a mean squared error of around 195 when compared to the actual point values. Hence the main reason I am posting here: to get some help from more experienced data scientists.

I've decided to include my work here, both for more experienced people to critique and maybe for some less experienced people to learn. This project was, again, done as a school project so please excuse some of my markdown comments as they had to follow a format for the class. This is also done in Python primarily using scikit learn for all data modeling and pandas for pre-processing. I used VS Code as my IDE with the Microsoft Python plugin to view and edit Jupyter Notebooks.

I want to keep developing this in the future, at this point not even to make money but just because I think it's a cool concept. The thought of math being able to better predict as complex a game as football more accurately than almost anyone is crazy. Other than this model, I recently also purchased a Raspberry Pi (also being used for other side projects) to eventually automatically pull new game data for the model to predict.

Like I said above please feel free to critique, this was basically my first major python project and I had no experience with any of these libraries. Also don't usually post on Reddit so if my formatting sucks call me out on that too.

Thanks guys, hope this is a helpful post to keep the subreddit going.

Jupyter Notebook: http://www.filedropper.com/finalproject_2 (not sure how long the site will host the file TBH)

**Top Comments:**

> **u/15woodsjo** (4 pts): To piggy back off this answer, I would also throw in a suggestion of using a neural network and turning this into a binary classification problem.

In practicality this is a logistic regression model that you have more control over, and can potentially get a little bit better of a model out of the algorithm.

&amp;#x200B;

The reason I would suggest anything binary classification for this type of problem is you would want to be able to measure the % likelihood of one team vs. another covering the spread whilst the line moves. In essence, you can get more information by knowing that team A has a 60% likelihood of covering a (-9) line and team B has a 40% chance PLUS team A has a 55% likelihood of covering a (-10) line and team B has a 55% chance. Basically you want to be able to apply your model to a dynamic line to get what is hopefully a more accurate picture of a +EV game
>
> **u/KidMcC** (3 pts): Will respond more fully later, but one thing that jumps out at me is that you might want to explore using a GLM with Poisson distribution as opposed to something like SVMs for football scores. This allows you a better probability assignment to different outcomes. 

Basic googling should land you more stats-focused details on that.

As an aside, there are better ways to handle imbalanced data than using an SVM for assigning binary winner/loser status. SVMs rarely perform consistently better than some other such models, like Logistic Regression or Random Forest Classifiers. Looking into weighted logistic regression or sub-sampling to balance out data as opposed to picking a specific model family as a result.

&amp;#x200B;

Again, will respond more later, as it's an interesting problem. Also open to debate re: any of the above.
>
> **u/15woodsjo** (2 pts): That's fair, my background is in basketball where I suppose there is a larger sample size.
>
> **u/KidMcC** (2 pts): This is a very important distinction. "Binary classification" can be done at least two ways here.   
1) Linear model (of sorts) fit to predict the point difference (homeScore - awayScore). Again, GLM approach with Poisson Distribution is the most common choice for football for a reason, given how scoring is not linear with each point-accumulating event. The sign of the endogenous variable would then be indicating the "win" the same way a 1/0 would in your example. Here you can use size of the difference to indicate probability, to some degree.   
[https://www.sbo.net/strategy/football-prediction-model-poisson-distribution/](https://www.sbo.net/strategy/football-prediction-model-poisson-distribution/)

[https://www.pinnacle.com/en/betting-articles/Soccer/how-to-calculate-poisson-distribution/MD62MLXUMKMXZ6A8](https://www.pinnacle.com/en/betting-articles/Soccer/how-to-calculate-poisson-distribution/MD62MLXUMKMXZ6A8)

2) Ignore points and predict an actual binary variable indicating whether or not the home team won. What this modeling approach provides is a direct probability associated with each classification. This also requires a choice to be made of regularization, L1/L2 penalty if using Logistic Regression, etc.  


Predicting scores via regression, and then daisy-chaining that back into a spread comparison to then take advantage of error profiling, like you said, is quite indirect and will certainly introduce more bias and/or volatility than what it returns in accuracy.
>
> **u/KidMcC** (2 pts): If we are talking about predicting binary game outcome, then I'd be hesitant to go the route of neural network. By its very nature of scheduling and season construction, football doesn't offer a huge dataset of games to really draw from (compared to other sports). Especially if you aren't weighting games from the distant past fairly, one can find themselves with a high variance, over-parameterized model fit on too little an amount of data. All my opinion of course! 

I do think a thoughtful feature selection process fit to an XGB or RandomForest model might be more manageable given that gameplay data gets old fast. Exponential weighting can be your friend here, though, if you need to go way back, just make sure your offense-profiling is dynamic!
>
> **u/15woodsjo** (2 pts): You are implementing a binary decision based on your model but not using an algorithm that is trained using binary classification. Slight difference
>
> **u/HamirTime** (2 pts): Thanks for the insight, I will definitely look into GLMs and their applications. I'm more familiar with logistic regression, so I would probably err towards looking into that to better handle imbalanced data
>
> **u/HamirTime** (2 pts): I could be misunderstanding your suggestion, but I think I am currently already transforming this into a binary classification problem. After using regression to calculate the score, I compare it with the spread to calculate a 'class' variable (0 or 1). 0 meaning a bet should be placed on the away team and a 1 meaning a bet on the home team. I use these to also measure common metrics like accuracy, precision, and recall.

 The likelihood percentages was also something I wanted to implement by using the difference between the predicted score and the spread, but wanted to focus on improving the model before then
>
> **u/anxiousalpaca** (1 pts): You are right, i totally misread what is meant by daisy-chaining back (not an English native speaker)
>
> **u/KidMcC** (1 pts): The OP said nothing of features describing the relative defensive capability of either side of the ball. Without such features, I'd still say daisy-chaining yhat values for score back into a comparison is risky, as it leaves nothing in the model reflecting the fact that for one team's offense to have the opportunity to score, it generally requires that the other team does not have the same opportunity at the same time (save for pick-6s). Volatility would be unstable when you begin to use this approach with games where disparity between defensive capability on each side is substantial. At least, this is what I have found. Curious to hear more if this is still at odds with your experience.
>

---

### [How do you deal with non-stationarity, infinite variance and distributional assumptions in sports data for betting models?](https://reddit.com/r/algobetting/comments/1jz4868/how_do_you_deal_with_nonstationarity_infinite/)
**Author**: u/Firm-Address-9534 | **Score**: 7 | **Comments**: 6 | **Date**: 2025-04-14

Hey all,

Layman explanation of non-stationarity:

Imagine you're tracking your team's performance week after week — maybe they're scoring more lately, or the odds for their win are shrinking. If the average numbers keep changing over time, that's non-stationary. It's like trying to aim at a moving target — your betting model can’t "lock in" a consistent pattern. Take this explanation with a grain of salt since it’s more complex than this simplification.

So historical data usually doesn’t reflect the current reality anymore. That’s why non-stationary data messes with prediction models — you think you’ve spotted a trend, but the trend already changed.  
  
Layman explanation undefined mean:

Normally, if you track enough results, you expect to find an average — like the typical number of goals in a match. But sometimes, there are so many extreme results (crazy high odds, or freak scores), that the average never settles. The more you track, the bigger it gets.

In simplified math terms:

This happens when the mean (average) doesn’t converge as sample size increases.

  
Layman explanation infinite variance:

Variance tells you how spread out the data is — like how far scores, corners, assists or odds swing from the average. If variance is infinite, it means you could see huge outliers often enough that you can't trust the spread at all.

In sports betting:

You might find odds or scorelines that are so extreme (say, a 200:1 correct score that hits more often than expected) that it wrecks any notion of what’s “normal.”  
Even if the average looks okay, you might suddenly hit a freak result that breaks your bankroll or model.

 

Layman explanation of distributional assumptions:

When you build a model, you often assume the data follows a specific “shape” — like a bell curve or a Poisson distribution. That shape is called a distribution.

Think of it like expecting:

Most football games to end 1–0, 2–1, 0–0, and only rarely 7–2

Or assuming odds behave in a way that fits a clean pattern, like normal distribution (the classic bell curve)

So, when we say, “distributional assumptions,” we're really saying:  
  
“I don’t know exactly what’ll happen, but I expect the numbers to behave kind of like this shape”  
  
Why Bad Assumptions Are Dangerous

 You underestimate risk:

Your model thinks rare results are “once in a decade” — but they happen every season.

Confidence intervals lie:

You think you have a 95% chance of winning a bet — but it's really 70%.

You miscalculated value:

You bet on “fair odds” based on the wrong distribution and lose long-term.  
  
Goals don’t follow Poisson or negative binomial as neatly as textbooks say  
  
Odds don’t reflect “pure probability” — they include public bias, team reputation, and market manipulation.  
  
Rare scorelines (like 5–4) aren’t that rare, but most models treat them like they are.  
  
  
I was thinking about implementing causal discovery and causal inference to better assess the problems that we face in the data.  
  
Any takes on this?

**Top Comments:**

> **u/Open_Future8712** (1 pts): Non-stationarity is tricky. I usually segment the data into smaller, more stable periods. For infinite variance, I use robust statistical methods like bootstrapping. Distributional assumptions? I prefer non-parametric methods. I’ve been using RobôTip for a while. It helps with soccer stats, making the betting process more data-driven and less guesswork.
>
> **u/Firm-Address-9534** (1 pts): 1- if the odds are  low enough you for sure can have 95% win rate.
0.25 of kelly criterion. Not 25% of your account, different things even if they converge to a close number in this example.
2- correct scores is liquid enough, offered by exchanges and sportsbook.
>
> **u/Badslinkie** (1 pts): Again, you're overestimating the similarities. For 1) You almost can't even place bets on odds long enough to give you a 95% win rate. I can't even think of a bet where they would take your action regularly at those odds, maybe betting 1 seeds ML every year in the NCAA tournament? If you're risking 25% of your BR on anything in sports betting you're going to get washed out. 2) You don't get to bet on whatever thing you want in this game, an operator has to offer it and they don't take a lot of money on the non main-stream bets. You're just never going to get down a significant amount of money on anything other than spreads and totals in this world.
>
> **u/Firm-Address-9534** (1 pts): Thanks for the comment.

It also depends on what you are betting, lets say you always bet on 3 or 4 most common correct scores. and you have 95% win-rate with it .in a bad streak where the results are skewed compared to what you previous thought was the mean.   
 Using kelly criterion at 0.25 you would loose 80% of the initial balance in 6 wrong bets.  


But i get your point of the losses being capped.
>
> **u/Badslinkie** (1 pts): You’re overthinking the relationship between finance and sports. 

In finance if you short GameStop and Reddit happens you lose infinity. In sports if two teams go to 16 overtime’s and score 6 sigma points and you’re on the under you just lose a bet.  In theory a 0 goal game happens with a similar frequency and these losses should wash. There’s just no world where a black swan event is wiping out 50% of your bank roll unless you’re risking that amount.
>
> **u/Firm-Address-9534** (1 pts): Im a quant and tbh most of the models in quantitative trading and risk are full of assumptions that are not met.
>
> **u/__sharpsresearch__** (1 pts): I like this question a lot. Iv spent a lot of time thinking about it and trying things. Iv taken a lot of my approaches from how people like Jane st look at markets (volatility as you mentioned but other time series variables, like differentials, Hurst, etc.) also a good parallel is weather forecasting.

Basically in the end imo, this is time series forecasting. And you can get a lot of what people are doing in finance and weather as they have done it for years and have spent a lot of money in the areas.
>

---

### [Looking for partner on CS2 betting project](https://reddit.com/r/algobetting/comments/1k76y3q/looking_for_partner_on_cs2_betting_project/)
**Author**: u/Stepanovich | **Score**: 6 | **Comments**: 0 | **Date**: 2025-04-24

Hi Team, will keep this short and sweet but I am looking for someone to pair up with on creating a betting syndicate for CS2. I am developing the trading platform using C# and will bet through Sport market API. If you have experience in C# and data science and want to be involved in this project, get in touch.

---

### [Distribution of Poisson : statistical prediction of scores](https://reddit.com/r/algobetting/comments/v33slu/distribution_of_poisson_statistical_prediction_of/)
**Author**: u/kassio92 | **Score**: 6 | **Comments**: 5 | **Date**: 2022-06-02

I have been working on a quantitative model using the Poisson distribution to calculate the probabilities of the scores of soccer games. This law of probabilities is used with historical data (average goal scored by team…).

Need some advices to make it more user-friendly.

[https://www.scorepredict.fr](https://www.scorepredict.fr)

**Top Comments:**

> **u/kassio92** (3 pts): Statistical pronostics 03/06/2022 :

France 2-1 Danemark Probability 8.68% ✅

Croatie 2-1 Autriche Probability 9.08% ✅

Belgique 1-1 Pays-Bas Probability 13.02% ✅✅

If you want to make your own statistical pronostic : https://www.scorepredict.fr
>
> **u/kassio92** (2 pts): Statistical pronostics 07/06/2022 :

Germany 2-1 England Probability : 9.65 %

Italia 1-1 Hungary Probability : 12.46 %

If you want to make your own statistical pronostic : https://www.scorepredict.fr
>
> **u/kassio92** (1 pts): https://plotly.com/python/heatmaps/
>
> **u/kassio92** (1 pts): It’s from plotly, you can also use seaborn
>
> **u/zoidbergisawesome** (1 pts): What are you using for heatmap? Which python lib?
>

---

### [Moving past the Basics (EPL)](https://reddit.com/r/algobetting/comments/psbvxy/moving_past_the_basics_epl/)
**Author**: u/ProdigyManlet | **Score**: 6 | **Comments**: 12 | **Date**: 2021-09-21

Hi everyone, I'm looking at creating an algorithm that predicts the outcome of EPL matches and provides the odds for value-seeking (seems the easiest place to start given the popularity and availability of data). The introductory approach seems to be modelling the expected goals scored by both teams using a Poisson distribution, which is a nice and intuitive model to start with (at least for someone with a bit of an applied stats background).

I'm now looking into more advanced classification methods that predict the outcome of a match between two teams. So far my classification model is getting 50% accuracy using only historical match result data (slightly transformed), so hopefully that's a good starting point. I've got some ideas for more features to add from reading a few papers and some intuition (e.g. manager data, weather, etc.), but was wondering what others found was effective or if they had any lessons learned in moving forward on the modelling side?

This might be too open ended, but some common themes and areas of interest I thought my be relevant to others are:

* How were people's experience with tmproving the basic models (e.g. Poisson) versus moving to classification models (e.g. traditional machine learning)?
* Aside from train/val/test data splits &amp; backtesting, what other techniques did people find effective for evaluating the accuracy or the reliability of their algorithm?
* Did anyone find any common misconceptions? (E.g. chasing down weather data only to find it's impact on model performance was limited).
* Any general types of data aside from match results/historical goal performance that were found useful?

**Top Comments:**

> **u/Davidweb1337** (3 pts): Im not experienced with running models or machine learning so i don't know what kind of data you're looking for. But from what I've heard in the industry, it's been very difficult to find live data feeds for League of legends, especially in China since the organisation running the tournaments over there are apparently not selling any live feeds to betting companies, often leading to latency issues and poor trading on the bookmaker's side. It's usually an esports trader manually adjusting odds while watching the stream haha. Or no live betting offered.

From what I could find, someone has already attempted to build a model here: (includes a link to a dataset, under downloads &amp; tools) https://www.quantumsportssolutions.com/blogs/league-of-legends/a-predictive-model-of-league-of-legends-game-outcomes
>
> **u/lequanghai** (2 pts): Where do you get data for esports? I mostly play and follow League of legends but cant find any complete dataset or source to perform analysis &amp; live betting.
>
> **u/Davidweb1337** (2 pts): E-sports is quite inefficient actually. It has only really started ramping up in the past few years but is still dwarfed by most traditional sports so bookmakers don't really invest as much into R&amp;D for it. You're very likely to find stale prices/lines here, but also very low betting limits.
>
> **u/bananarepubliccat** (2 pts): Yes,  most of the things you mention perform pretty poorly in reality.

Rolling window methods aren't that useful. You want to use season data with possibly priors from the previous season. Again, it is how information gets incorporated. With filter models, the update cycle is capturing all the right information...with rolling windows, you are getting some approximation of skill using unimportant information (against weak opponents, very old matches, etc.). You can weight more recent matches but it still won't beat ELO.

Btw, I didn't make this totally clear in my previous comment: the reason why these sports are hard to model is because the data is adversarial. The information comes from interactions between two teams, it is not only team skill but opponent skill that matters. This is particularly bad in football because you can have teams that win by doing things that would cause other teams to lose (this is less common in other invasion sports where there is usually a dominant strategy)...for example, if you have a model based on possession, teams that counter-attack will be rated poorly...and even then, that counter-attack strategy may only work against certain kinds of teams. And then you have a difference between offensive and defensive strategies: for example, Newcastle always used to outperform vs good teams because they were so defensively solid, but lost it whenever they had to attack the other team. It is very tricky. So an ELO model that has far less data will outperform because the ratings and difference of ratings capture the maximum amount of information.

If you are able to use some non-parametric grouping and then incorporate that into your rating then I think you would be able to produce a more traditional ML model that works (i.e. this team is a counterattack team against an attacking team so we expect X fast breaks, and they got X+5 so we increase their rating)...but even then, I still think the update cycle of filter models like ELO is very effe [...]
>
> **u/king-chungus** (2 pts): Don’t do deep learning, but I definitely think log regression, SVMs, etc… can be viable
>
> **u/ProdigyManlet** (2 pts): Thanks for the extremely detailed reply, this is absolutely awesome and is riddled with great info that answers a whole bunch of my questions (and some I hadn't even thought of yet).

By classification and traditional machine learning I'm referring to things like logistic regression, decision trees/random forest, support vector machines, etc. Basically traditional machine learning is non-deep learning methods. I definitely think Deep Learning would perform pretty poorly in most betting algos given the small data quantities.

In terms of data, I was using a rolling window (e.g. N games like you mentioned) that rolled across prior seasons to avoid the issue of say if N = 20, but we're at match 5 then there's only 4 data points. Obviously a lot changes between seasons which is not accounted for, but I was hoping to factor in information that captured these changes later on (i.e. manager changes/metrics and some form of player metrics). The Brier score looks good, and I like the idea of the ELO approach as it's much more manageable, simple and looks like it will be less reliant on across-season data; will look into all of these.

I had a feeling that the bigger markets will be more difficult. I will still try to get my basic model framework up and running using EPL, and then switch to some local leagues in my own country (looks like I can get the same data in basically the same format so should be an easy switch). I wanted to stick with a sport I have good domain knowledge in as I want to keep it interesting as a hobby while reviewing my classical statistics knowledge (I'm experienced in Deep Learning and Traditional ML, but it's been a while since I went back to the basics of distributions). However, I'll definitely take the suggestion onboard and look at some more obscure markets on the side. I was thinking of E-Sports but I would assume that might be quite efficient too.
>
> **u/TraptInaCommentFctry** (1 pts): &gt;you only update when you see something unexpected, the whole measure is weighted against peers

could you clarify what you mean by this?
>
> **u/bananarepubliccat** (1 pts): That isn't what I said.

I have used data that costs $100k+ annually, the features don't matter if you start from the wrong place (I explained this above, if you are seeing similar predictive power from ELO as ML then you have gone very wrong because ML, as most people are doing it, doesn't work...tbf, most people don't do ELO right either but that isn't a problem with the model). This varies by sport but the OP asked about soccer.

Using ELO as a feature is a basic error (and again, you are missing the point massively). ELO is just a filter, so you can use your ML model as an input to ELO: it is just a map from joint distribution of skill to prediction for a feature, so you can use ML as an input to ELO (I wouldn't advise building a mixture with ELO either, that is a very bad idea practically for soccer because of lineup changes).

How you do this is more complex but the key is that you are modelling a joint probability, that is where the power comes from. What OP will have tried is: X feature over N games or something similar, these models don't work (you can modify features, but it still won't get close). You can get them into a joint probability but, again, the problem is that they don't represent information correctly (again, this is obvious when you think carefully about what you are actually modelling...most people, inadvertently, end up with a single distribution for the average team...this works particularly poorly in soccer where there is no strategic equilibrium i.e. the meaning of features varies hugely based on the team).
>
> **u/MathMod3ler** (1 pts): Thanks for clarifying the original comment. Respectfully, I disagree that traditional ML is incapable of handling that amount of information. I think it comes down to having good features. Although, in practice I prefer using several ELO models as features in my ML models. So I definitely like the information ELO captures.
>
> **u/MathMod3ler** (1 pts): I disagree with a lot of this thread. Although, I think reasonable minds can disagree on this sort of stuff. I would say a couple things to take your modelling to the next level:

1)Stack uncorrelated models.
2) Use the betting market as a starting point for some of your models. The betting market is already a damn good model. Build on top of it, it already takes into account many of the basic features (probably including Poisson Distribution of goals). 
3) Come up with different targets. Ex: Win-Loss Binary and Difference in goals (they both tell you the betting outcome but the computer will look at them very differently).
4) Have way bigger test-validation sets than the normal rules of thumb. Finding patterns is easy...finding persistent patterns is hard.

My two cents, classification is fine. Just really do a lot of safe-guards and validation.
>

---

### [NFL Passing Attempts Model Advice](https://reddit.com/r/algobetting/comments/1k67adj/nfl_passing_attempts_model_advice/)
**Author**: u/toddinvesterguy12 | **Score**: 5 | **Comments**: 7 | **Date**: 2025-04-23

Hey everyone, I just tried for the first time to build a model that predicts a players pass attempts. I collected 3 years of data via scraping/APIs with columns formatted as 

Date of game,
Player,
Pass attempts in game,
Players team at time of game,
Home/Away,
Opponent team,
Player’s Coach,
Game start time,
Location of game,
Average temperature during 4 hours from start of game time,
Type of precipitation if any,
How many hours in four hour window precipitation occurred,
Pre game points total at fanduel and DraftKings,
Pre game total odds at fanduel and DraftKings,
Pre game spread for players team at fanduel and DraftKings,
Pre game spread odds for players team at fanduel and DraftKings,
Pregame pass attempts total at fanduel and DraftKings,
Pregame pass attempts odds at fanduel and DraftKings

I have minimal experience with coding (2 intro level courses in python and R), so I loaded this data into Claude and promoted it to create linear regression and random forest models with the data. I prompted it to train on half and test on the other half. Both achieved an r2 of around 0.4 so not good. 

At this point, I’m curious if I’m trying to predict a metric that is too volatile, if I need more data using the same features, if I need to add additional features, a combo, or if I’m missing something else I should learn about before proceeding. 

Appreciate any advice.

**Top Comments:**

> **u/cortezzzthekiller** (6 pts): Props are generally about predicting volume -- and passing attempts is ALL about volume. So you are missing a huge part of the puzzle here -- off/def plays per game
>
> **u/2kungfu4u** (2 pts): Huge agree here. I'd also argue in tandem with that you'd mostly likely want to include metrics like pass rate over expectation, pass rush splits on a given team and maybe even team record. It's one thing to include the spread indicating if they're a dog or not but how often they are a dog is valuable as well imo
>
> **u/Golladayholliday** (2 pts): I mean… What is the point of this model? To beat the books? To do some learning? 

You included the book odds, any good model is just going to violently latch on to that with the other things you have included(missing some major pieces). You very likely have built a devigger 😂. This is where the journey starts tho. Keep on pushing. 

I think the best piece of advice I can give you is what I wish someone had told me. ML/AI isn’t magic, it’s an extension of your expertise. You can huck a bunch of data at a model and you might get a okay baseline, but that is not what makes a model great. You need the domain knowledge and ML knowledge to know what is important and how to present (feature engineer) it, and if done right it will come to very similar conclusions as an expert would. 

The difference is it can do it in less than a second instead of an in depth time consuming expert review. That’s the magic.
>
> **u/Golladayholliday** (1 pts): It’s going to be tough only because you’re essentially feeding a much better model back into your model as an input that’s likely considering all the same things you are plus a lot more. 

The other thing to accept is most bets there is no +EV side. I have a very solid baseball model, and if I had to estimate about 80% of the time I get some number that’s between the spread(both sides lose money long term), 10% it’s very light value (picking up a quarter or 2 of EV on my $50 bet) and 10% it’s decent.
>
> **u/toddinvesterguy12** (1 pts): Essentially I want to connect the predictions it makes to +EV sides on passing attempt bets. For now I just need to learn more about machine learning and how best to present data to these models and I really appreciate your insights
>
> **u/toddinvesterguy12** (1 pts): Appreciate it that’s a great idea
>

---

### [How useful is something like this](https://reddit.com/r/algobetting/comments/1k662a4/how_useful_is_something_like_this/)
**Author**: u/Forsaken-Hearing3540 | **Score**: 4 | **Comments**: 17 | **Date**: 2025-04-23

www.playerprobabilities.com

I’ve been working on a machine learning model to predict NBA player props — specifically points, assists, and rebounds. Originally, I used linear regression (with Lasso for feature selection) and rolling averages to predict raw values. That alone gave me around 57  - 70% accuracy on some given days, this is for 68+ players on game days.

Now I’ve taken it a step further:
I treat the regression prediction as a mean,
Calculate a confidence interval using a z-score (95% confidence),
Run Monte Carlo simulations to estimate the distribution of outcomes,
Then compute the probability a player hits the over/under line.

Also a second reason why I am here ,can you guys share any tips on how you guys account for lineup changes and how it affects what a player is going to score. I have really been struggling with that aspect of things.l

---

### [Need help with a simple regression model](https://reddit.com/r/algobetting/comments/qgivhc/need_help_with_a_simple_regression_model/)
**Author**: u/[deleted] | **Score**: 4 | **Comments**: 10 | **Date**: 2021-10-26

Hi, I am in a Business Analytics class and have a project requiring me to build a simple logistic regression model to predict in-game NFL win probability.

It was fairly simple and I pretty much got it down, except one small problem. The win probability for the winning team should be 100% by the end of the 4th quarter, however, my model is not able to calculate this. I feel like there is a simple solution but my brain is not quite grasping it (worst feeling LOL).

Can anybody assist? Thank you very much in advance :&gt;

---

### [Exploring In-Game Predictions with Odds Data – Would like to Collaborate](https://reddit.com/r/algobetting/comments/1hni8vu/exploring_ingame_predictions_with_odds_data_would/)
**Author**: u/97wschultz | **Score**: 3 | **Comments**: 2 | **Date**: 2024-12-27

Hi everyone,

I’ve been working on a project where I collect odds data at 40-second intervals for EPL and Championship matches, with the goal of exploring whether in-game predictions can be made using this data alone.

I’ve had some promising results so far with models like XGBoost and logistic regression, but there’s plenty of room to build on this. My main focus is on expanding the models and gaining a deeper understanding of the possibilities.

This is more about learning and experimentation than making money. If anyone is interested in getting involved or exchanging ideas, I’d love to collaborate and see where this could lead!

---

### [NBA scores predicting](https://reddit.com/r/algobetting/comments/1flxcib/nba_scores_predicting/)
**Author**: u/FireDragonRider | **Score**: 3 | **Comments**: 26 | **Date**: 2024-09-21

Yesterday I finally invented a way to predict NBA games. Maybe 🤔 

I use NBA API, calculate some averages, then I ask GPT about them, then create some embedding vectors, then logistic regression. In the end I have probabilities of a team scoring more than each possible score plus minus 20 from the real score. So the first 20 should have a higher probability of "more", the second 20 should have a higher probability of "less". 

What do you think is the best way to test this algorithm? What metrics should I use to test it well and either against bookmaker predictions or at least against real scores, comparing the average accuracy to bookmakers?

---

### [Anyone know the status of MySportsFeeds.com?](https://reddit.com/r/algobetting/comments/105q4et/anyone_know_the_status_of_mysportsfeedscom/)
**Author**: u/postrema19 | **Score**: 2 | **Comments**: 4 | **Date**: 2023-01-07

Hi All.  Long time lurker/first time poster.  I have a background as software developer and am very interested in this space, but am finding it difficult locating a good source of historical data and/or feeds.

I  recently stumbled across what looked to be a promising API provider at [MySportsFeeds.com](https://MySportsFeeds.com), but have found them to be unresponsive.   The API and data modeling seem to be pretty mature and well organized, but I recently found that it is not returning data for NCAAM basketball, so I'm beginning to wonder if this site is now defunct.

Does anyone have any insight into the status of this provider?  If not, any recommendations in terms of other providers in this area would be well appreciated.  I am primarily interested in data for the "big four" of the US (NFL, MLB, NBA and NHL) as well as college basketball data.

Any help or direction is greatly appreciated!

---

### [Best way to use past XG data as a model feature for pre-match betting?](https://reddit.com/r/algobetting/comments/x4xgs3/best_way_to_use_past_xg_data_as_a_model_feature/)
**Author**: u/Bhagafat | **Score**: 1 | **Comments**: 5 | **Date**: 2022-09-03

If I have data sets such as from Understat which include XG, I can create a model off the back of this to predict things like final score, o2.5 yes/no, etc. for each match and backtest this. 

However without some kind of feature engineering for XG so that we have these features available to us before each game (e.g. avg XG past 6 games, etc.) this model would be useless for pre-match betting, because of course I don't know what the XG stats of a match will be until it happens.

I see a lot of people blindly resort to using Poisson probabilities, taking lambda to be the XG mean over x amount of games (inc. maybe some home/away weighting), but as accurate as Poisson can be it of course has its downfalls. I'd be interested to see if anyone has done some investigation into how to produce the best "pre-match statistics" involving XG. Has anybody got any links/reports/videos/etc. with some kind of discussion on best practices for feature engineering here?

Cheers

---

## Backtesting & Validation

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [Tennis Analysis #2: Upset Victories](https://reddit.com/r/algobetting/comments/11v0289/tennis_analysis_2_upset_victories/)
**Author**: u/quant_boy123 | **Score**: 12 | **Comments**: 1 | **Date**: 2023-03-18

Hello everyone,

It has been a while since I started what was supposed to be a series focused on tennis analysis from a sports betting perspective. In my first [post](https://www.reddit.com/r/algobetting/comments/ujmpv7/tennis_analysis/), I gave some insights into my motivation and an overview of my data. I also discussed two topics, Implied vs. Realized Probability in tennis betting and O/U Game Lines (theory vs. reality). Moreover, I conducted some backtests based on very simple strategies.

&amp;#x200B;

* Background

My goal for the future is to post more frequently and thereby give you all some trading ideas and valuable insights into tennis analytics. I will typically start with some theory, derived statistics and eventually show some real world betting strategies based on the findings. Whether they would be profitable or not is irrelevant, as both can provide important insights. A bad bet not taken is probably equally valuable as a good bet.

&amp;#x200B;

* Data

For this article, I am only looking at men’s results in official matches for which I have a minimum threshold of data required for the research. My dataset has been growing rapidly recently, since all tournaments have started to resume from the COVID break. Overall, 2022 saw a similar amount of matches as 2016-2019 did (roughly 30000 with clean data) and 2023 is on track to match that. It is important to note that both the quality and quantity of data increased steadily, with more than 60% of the high quality data coming from years &gt;2015.

&amp;#x200B;

* Surprising Outcomes

Today I want to look at upset victories/wins. My definition of an upset is based on bookmaker odds, not on ranking or any other statistics. Bookmaker odds reflect the best guess for the outcome of a match in an efficient market, since they not only take into account the ranking of the two players or their form, but also factors such as the surface, head to head outcomes between the two players and more. Therefore, an upset win can be defined as a win of a player with odds greater than a threshold, let’s say 3 (= Implied Probability roughly 30%, adjusted for vig). 

Firstly, I filter the data to only include players with at least 20 completed matches. Secondly, I exclude players with less than 5 upset wins. Then I start with looking at upset wins with a threshold odd of 3, so every win of a player with odds &gt;3 qualifies as upset win. Since surprises tend to scale with matches played, I rank the outcome by the percentage of upset wins to total matches the player entered as an underdog with odds &gt;3.

Most players making the top 50 of that statistics are ‘newer’ players. This has to do with the fact that most of the high quality data is from recent years, as explained in the Data section. Thus, upset wins from players like Novak Djokovic or Roger Federer are very unlikely, since the data is mainly from a time when they were entering almost every match as a favorite and if they were an underdog, it was typically not with odds &gt;3. 

It is straightforward to see that upset victories typically come at the early stages of the career of a tennis player. That is, when the bookmakers do not have enough information about a players skill. Once they have made some surprising wins, bookmakers lower the odds of the player in subsequent matches to reflect the updated information about their skill level more accurately. Their next wins may therefore not qualify as upset wins anymore, since the odds can be significantly lower than the threshold. This becomes obvious when looking at the odds history of a player like Carlos Alcaraz.

[Graph 1: Carlos Alcaraz ranking vs rolling median odds with a window length of 25 matches.](https://preview.redd.it/k4ugps6iyjoa1.png?width=432&amp;format=png&amp;auto=webp&amp;v=enabled&amp;s=ad92a53e46c91a5f801f8693b075dde24a266b77)

In this graph, the median odds with a rolling window of 25 matches are used. This has the advantage that the curve is smooth and a trend can be easily spotted. Median odds are used instead of average, since the average can plateau on a high level due to one match against a top opponent, for instance Nadal in the French Opens, with very high odds.

In his early days in 2019, when he was first competing in challengers and mainly futures, he often was the underdog. After quick initial success, however, he mainly entered futures tournament matches as the favorite. The same happened in challenger matches in 2020, when he dominated almost every tournament he entered. In 2021, he shifted focus to main tour events, where he often was the underdog. This is where his median odds increase again. In 2022 he had some great victories in the main tour, thus his odds decreased and are now among the lowest of all players, making him the favorite in almost any matchup.

In the following graph, we follow a simple strategy: bet 1 unit on Alcaraz whenever the odds are &gt;3. Obviously, this is with a good portion of hindsight and not a f

[... truncated, see original post ...]

**Top Comments:**

> **u/zahaha** (1 pts): As someone who just got into modeling Woman's Tennis, these are amazing. Please keep it up!

You ever look at live betting trends? Im sure its very hard to get the historical live lines but im curious if there are any situations when "if the pre match odds are &gt;-200 and the live line gets to +300, always take it", or stuff like that.
>

---

### [Common Questions](https://reddit.com/r/algobetting/comments/119hp1j/common_questions/)
**Author**: u/zahaha | **Score**: 10 | **Comments**: 4 | **Date**: 2023-02-22

TLDR: What are the main questions that you have/had as a beginner and what resources are you looking for but hard to find?

I am relatively new to Algo betting and have not found it easy to find good resources around modeling, statistical strategies, programming, etc.  I think that a consolidated list of all kinds of resources could benefit everyone.

I have started to keep a small list myself and would like to build it out to include a wide variety of topics. I will make it public so everyone can view it. But first I want to compile a list of Topics. What are other topics related to all things Algobetting that should be included on this list? This is what I have so far:

**Programming**

* Python/R
* Learn Python/R
* Data Scraping
* Prewritten Code Sets

**Data**

* Best resources for historical stats, box scores, Odds, etc by sport
* Best resources for current market odds
* Odds Screens
* API's

**Models and Statistics**

* Resources for Learning about statistics (particularly those relevant to sports modeling) 
* Types of Models
* Examples by sport

**Best Media Related to Sports Betting and Modeling** 

* YouTube Videos
* Podcasts
* Books
* Articles/Blogs
* Twitter Follows

**Top Comments:**

> **u/zahaha** (2 pts): Yep, I've seen this pinned post and its a good starting point. However it's lacking resources for many of the common questions and isn't organized. 

I would like to improve on this with a more comprehensive and organized list.
>
> **u/stander414** (2 pts): https://www.reddit.com/r/algobetting/comments/g5hi6j/creating_a_collection_of_resources_to_introduce
>
> **u/ENTP_Geek** (1 pts): How is this going? Have you added much to your list?
>

---

### [MMA AI &amp; Project Sharing](https://reddit.com/r/algobetting/comments/jzhyqk/mma_ai_project_sharing/)
**Author**: u/akkatips | **Score**: 9 | **Comments**: 3 | **Date**: 2020-11-23

Recently, we've created an MMA AI which predicts the outcome of UFC fights. There are numerous variables used ranging from each fighter's reach to the number of KO wins they've had in the UFC to the number of strikes they threw last fight. All these variables are inputted into the AI each week and as a result generates predictions. 

The backtesting of the AI gave us some very promising results (Since Jan 2019):

**Total Profit: +49.63U** 

**Average Profit per Event: +0.64U**  

**Average ROI: +8.67%** 

**Here are the graphs showing this in a more visual format:** [**https://imgur.com/a/Fdu0oSq**](https://imgur.com/a/Fdu0oSq)

We have also been working on an extra MMA AI that aims to predict whether a fight will go the distance or not. Last weekend we were able to combine the predictions from both AIs to predict a 6.50 odds winner at the weekend, we even pre-posted it on Reddit!

Has anyone else been working on some interesting projects and found profitable strategies as a result?

**Top Comments:**

> **u/bluelotus214** (1 pts): Wicked.  I'm looking for some data on this.
>
> **u/RepresentativeDig921** (1 pts): Strategy.

Bet every single MMA dog like this

Win

By TKO, KO

By Submission

Profit.
>
> **u/plinifan999** (1 pts): Hello! Several questions:

\--How do you get your data?

\--What type of model are you using?
>

---

### [Best place to get historical esports (CSGO) odds](https://reddit.com/r/algobetting/comments/10yu2mf/best_place_to_get_historical_esports_csgo_odds/)
**Author**: u/goatcs | **Score**: 8 | **Comments**: 8 | **Date**: 2023-02-10

Hello,

&amp;#x200B;

To practice my python skills I want to create a model that will try and predict pro csgo games. I was wondering if anyone has a good source for historical odds as I am not really finding anything particularly useful in my searches.

Furthermore, does anyone have any good sources for csgo data in general, I am aware of HLTV api on github [https://github.com/gigobyte/HLTV](https://github.com/gigobyte/HLTV).

&amp;#x200B;

EDIT:  


Ideally I would like a full dataset of the last 2 years games, showing the map, the 2 teams that played, if it was lan or online, the odds for each map (odds for other things like rounds etc. would be amazing), who won, the date it was played, the score at half time, the scoreboard (at half time as well would be awesome). I should be able to get most of this through the hltv api but if anyone has any suggestions or better ideas that would be great because getting all this data will be time consuming.

&amp;#x200B;

Thanks in advanced.

**Top Comments:**

> **u/Ok-Seaworthiness3874** (2 pts): sure! and check my edit on the previous comment about scrapers. I think that's ur best way to start collecting data realistically. I used to make web scrapers in my past job so if you need any pointers lmk. I think selenium library is also really good if you want to stick with python.
>
> **u/Ok-Seaworthiness3874** (2 pts): I do a lot of Dota 2 esports betting, like 10k a week in bets placed - and I have thought about trying to do something similar with Dota open api data. I do wonder how useful 2 year old data actually is for any E-sport. At least with Dota, there are very tranforming updates that release ever 3 months or so, that kind of nullifies old data as it relates to win probability with certain heroes and whatnot.

Also, rosters change VERY frequently in Dota. Usually 1-2 times per year, rosters will change either a couple players or the entire team. I wonder if it's the same with CS:GO, where data from even a year ago would provide little to no insight into their current strength as a team.

If such is the case with CSGO as it is with Dota 2, I would focus on much more recent data. I find with e-sports in general teams go on very hot streaks, or they play well in against certain regions while playing poorly against other regions. THis could have more to do with the heroes that certain regions tend towards, and how those micro-meta's clash when in Major LAN matches. I know a lot of CSGO meta revolves around the $$$ made between rounds, and how that might help certain teams who battle better with certain weapons or whatever. It might be worth considering like what is their probability of winning with less gear, vs more gear for a given round, on a given map, vs a given team. Some teams might be trash at pistol round but insane if you give them an AWP (I don't really follow GO closely, so I wouldn't know).

But in general, I'm not sure 2 year old data would be helpful. It's a different game, with different meta, and different team rosters I would reckon.
>
> **u/Gurubusters** (1 pts): You can get free 1 minute odds data at [https://historicdata.betfair.com/#/home](https://historicdata.betfair.com/#/home) if you have a betfair account. It should be in 'Other Sports'. For more advanced data, you'd have to pay.
>
> **u/goatcs** (1 pts): what do you believe the 2 big meta shifts were? I know there have been map changes and changes to the M4 but I don't believe these were massive meta shifts, unless I am missing something.
>
> **u/ScooobySnackks** (1 pts): CS has has 2 massive meta shifts over the past year and a half. You’re going to need to segregate any map level data between the 2 metas. Otherwise you’re gonna miss the mark
>
> **u/goatcs** (1 pts): thanks, i will take a read of these
>
> **u/Ok-Seaworthiness3874** (1 pts): That's true - Dota is a lot more teamwork intrinsic, where the hero you pick is reliant on what your teammates pick and are good at. Making one player with his specific hero pool, maybe a poor fit in general for a team that can't support it. Where CSGO players can essentially perform mostly the same on different rosters.

I know i've been able to find a few Dota 2 win probability doctoral thesis' online just by searching. You could maybe search for something similar for CS:GO to see if somebody has published a journal about it that could lead you in the right direction.

Here's one I found for you: [https://dspace.cvut.cz/bitstream/handle/10467/99181/F3-BP-2022-Svec-Ondrej-predicting\_csgo\_outcomes\_with\_machine\_learning.pdf](https://dspace.cvut.cz/bitstream/handle/10467/99181/F3-BP-2022-Svec-Ondrej-predicting_csgo_outcomes_with_machine_learning.pdf)

&amp;#x200B;

[https://publications.lib.chalmers.se/records/fulltext/256129/256129.pdf](https://publications.lib.chalmers.se/records/fulltext/256129/256129.pdf)

&amp;#x200B;

[**https://osf.io/u9j5g/download**](https://osf.io/u9j5g/download)

My guess is some web scraping will absolutely be needed to pull this off. Building a web scraper is quite easy - and you can use ChatGPT to help. For instance, say in ChatGPT "Create a web scraper using puppeteer (A JS library I use) that stores the value of element \[figure out what this element name is using a chrome plugin or whatever\] every \[time interval\] or everytime the element changes". That should get you started. Then you'll have to think creatively about how you plan to sync those odd's with the actual game time. YOu would likely need two scrapers running side-by-side, one that's pulling odds, and one that's pulling current match data. (real-time, as I know dota has a 5 minute delay on stream, but a 1 minute API delay that books use to create odd's in a algorithm - check [hawk.live](https://hawk.live) if you want to know what I mean). Basically Dota 2 servers can [...]
>
> **u/goatcs** (1 pts): I agree with you, esports moves very fast compared to the typical sports so in my opinion 2 years data in csgo may not be as useful as 2 years data in football. I wanted to start with a 2 year dataset so I can do tests and see if old data will have impact.

I don't really know much about Dota but in CSGO there aren't really any transforming updates (at least in the last 2 years), the biggest updates are often just a new map in the map pool with an old map being taken out, this should be fairly easy to track as you can easily filter out maps not in the map pool.

Roster changes is something I will need to take into account and I agree 2 years roster data will show very little insight as teams can completely change multiple times in that time span. However, I believe 2 years data will be more useful for individual player stats as the game hasn't changed enormously in that timespan. So hopefully 2 years data will show some insight into player strengths.
>

---

### [How do you deal with non-stationarity, infinite variance and distributional assumptions in sports data for betting models?](https://reddit.com/r/algobetting/comments/1jz4868/how_do_you_deal_with_nonstationarity_infinite/)
**Author**: u/Firm-Address-9534 | **Score**: 7 | **Comments**: 6 | **Date**: 2025-04-14

Hey all,

Layman explanation of non-stationarity:

Imagine you're tracking your team's performance week after week — maybe they're scoring more lately, or the odds for their win are shrinking. If the average numbers keep changing over time, that's non-stationary. It's like trying to aim at a moving target — your betting model can’t "lock in" a consistent pattern. Take this explanation with a grain of salt since it’s more complex than this simplification.

So historical data usually doesn’t reflect the current reality anymore. That’s why non-stationary data messes with prediction models — you think you’ve spotted a trend, but the trend already changed.  
  
Layman explanation undefined mean:

Normally, if you track enough results, you expect to find an average — like the typical number of goals in a match. But sometimes, there are so many extreme results (crazy high odds, or freak scores), that the average never settles. The more you track, the bigger it gets.

In simplified math terms:

This happens when the mean (average) doesn’t converge as sample size increases.

  
Layman explanation infinite variance:

Variance tells you how spread out the data is — like how far scores, corners, assists or odds swing from the average. If variance is infinite, it means you could see huge outliers often enough that you can't trust the spread at all.

In sports betting:

You might find odds or scorelines that are so extreme (say, a 200:1 correct score that hits more often than expected) that it wrecks any notion of what’s “normal.”  
Even if the average looks okay, you might suddenly hit a freak result that breaks your bankroll or model.

 

Layman explanation of distributional assumptions:

When you build a model, you often assume the data follows a specific “shape” — like a bell curve or a Poisson distribution. That shape is called a distribution.

Think of it like expecting:

Most football games to end 1–0, 2–1, 0–0, and only rarely 7–2

Or assuming odds behave in a way that fits a clean pattern, like normal distribution (the classic bell curve)

So, when we say, “distributional assumptions,” we're really saying:  
  
“I don’t know exactly what’ll happen, but I expect the numbers to behave kind of like this shape”  
  
Why Bad Assumptions Are Dangerous

 You underestimate risk:

Your model thinks rare results are “once in a decade” — but they happen every season.

Confidence intervals lie:

You think you have a 95% chance of winning a bet — but it's really 70%.

You miscalculated value:

You bet on “fair odds” based on the wrong distribution and lose long-term.  
  
Goals don’t follow Poisson or negative binomial as neatly as textbooks say  
  
Odds don’t reflect “pure probability” — they include public bias, team reputation, and market manipulation.  
  
Rare scorelines (like 5–4) aren’t that rare, but most models treat them like they are.  
  
  
I was thinking about implementing causal discovery and causal inference to better assess the problems that we face in the data.  
  
Any takes on this?

**Top Comments:**

> **u/Open_Future8712** (1 pts): Non-stationarity is tricky. I usually segment the data into smaller, more stable periods. For infinite variance, I use robust statistical methods like bootstrapping. Distributional assumptions? I prefer non-parametric methods. I’ve been using RobôTip for a while. It helps with soccer stats, making the betting process more data-driven and less guesswork.
>
> **u/Firm-Address-9534** (1 pts): 1- if the odds are  low enough you for sure can have 95% win rate.
0.25 of kelly criterion. Not 25% of your account, different things even if they converge to a close number in this example.
2- correct scores is liquid enough, offered by exchanges and sportsbook.
>
> **u/Badslinkie** (1 pts): Again, you're overestimating the similarities. For 1) You almost can't even place bets on odds long enough to give you a 95% win rate. I can't even think of a bet where they would take your action regularly at those odds, maybe betting 1 seeds ML every year in the NCAA tournament? If you're risking 25% of your BR on anything in sports betting you're going to get washed out. 2) You don't get to bet on whatever thing you want in this game, an operator has to offer it and they don't take a lot of money on the non main-stream bets. You're just never going to get down a significant amount of money on anything other than spreads and totals in this world.
>
> **u/Firm-Address-9534** (1 pts): Thanks for the comment.

It also depends on what you are betting, lets say you always bet on 3 or 4 most common correct scores. and you have 95% win-rate with it .in a bad streak where the results are skewed compared to what you previous thought was the mean.   
 Using kelly criterion at 0.25 you would loose 80% of the initial balance in 6 wrong bets.  


But i get your point of the losses being capped.
>
> **u/Badslinkie** (1 pts): You’re overthinking the relationship between finance and sports. 

In finance if you short GameStop and Reddit happens you lose infinity. In sports if two teams go to 16 overtime’s and score 6 sigma points and you’re on the under you just lose a bet.  In theory a 0 goal game happens with a similar frequency and these losses should wash. There’s just no world where a black swan event is wiping out 50% of your bank roll unless you’re risking that amount.
>
> **u/Firm-Address-9534** (1 pts): Im a quant and tbh most of the models in quantitative trading and risk are full of assumptions that are not met.
>
> **u/__sharpsresearch__** (1 pts): I like this question a lot. Iv spent a lot of time thinking about it and trying things. Iv taken a lot of my approaches from how people like Jane st look at markets (volatility as you mentioned but other time series variables, like differentials, Hurst, etc.) also a good parallel is weather forecasting.

Basically in the end imo, this is time series forecasting. And you can get a lot of what people are doing in finance and weather as they have done it for years and have spent a lot of money in the areas.
>

---

### [Distribution of Poisson : statistical prediction of scores](https://reddit.com/r/algobetting/comments/v33slu/distribution_of_poisson_statistical_prediction_of/)
**Author**: u/kassio92 | **Score**: 6 | **Comments**: 5 | **Date**: 2022-06-02

I have been working on a quantitative model using the Poisson distribution to calculate the probabilities of the scores of soccer games. This law of probabilities is used with historical data (average goal scored by team…).

Need some advices to make it more user-friendly.

[https://www.scorepredict.fr](https://www.scorepredict.fr)

**Top Comments:**

> **u/kassio92** (3 pts): Statistical pronostics 03/06/2022 :

France 2-1 Danemark Probability 8.68% ✅

Croatie 2-1 Autriche Probability 9.08% ✅

Belgique 1-1 Pays-Bas Probability 13.02% ✅✅

If you want to make your own statistical pronostic : https://www.scorepredict.fr
>
> **u/kassio92** (2 pts): Statistical pronostics 07/06/2022 :

Germany 2-1 England Probability : 9.65 %

Italia 1-1 Hungary Probability : 12.46 %

If you want to make your own statistical pronostic : https://www.scorepredict.fr
>
> **u/kassio92** (1 pts): https://plotly.com/python/heatmaps/
>
> **u/kassio92** (1 pts): It’s from plotly, you can also use seaborn
>
> **u/zoidbergisawesome** (1 pts): What are you using for heatmap? Which python lib?
>

---

### [Moving past the Basics (EPL)](https://reddit.com/r/algobetting/comments/psbvxy/moving_past_the_basics_epl/)
**Author**: u/ProdigyManlet | **Score**: 6 | **Comments**: 12 | **Date**: 2021-09-21

Hi everyone, I'm looking at creating an algorithm that predicts the outcome of EPL matches and provides the odds for value-seeking (seems the easiest place to start given the popularity and availability of data). The introductory approach seems to be modelling the expected goals scored by both teams using a Poisson distribution, which is a nice and intuitive model to start with (at least for someone with a bit of an applied stats background).

I'm now looking into more advanced classification methods that predict the outcome of a match between two teams. So far my classification model is getting 50% accuracy using only historical match result data (slightly transformed), so hopefully that's a good starting point. I've got some ideas for more features to add from reading a few papers and some intuition (e.g. manager data, weather, etc.), but was wondering what others found was effective or if they had any lessons learned in moving forward on the modelling side?

This might be too open ended, but some common themes and areas of interest I thought my be relevant to others are:

* How were people's experience with tmproving the basic models (e.g. Poisson) versus moving to classification models (e.g. traditional machine learning)?
* Aside from train/val/test data splits &amp; backtesting, what other techniques did people find effective for evaluating the accuracy or the reliability of their algorithm?
* Did anyone find any common misconceptions? (E.g. chasing down weather data only to find it's impact on model performance was limited).
* Any general types of data aside from match results/historical goal performance that were found useful?

**Top Comments:**

> **u/Davidweb1337** (3 pts): Im not experienced with running models or machine learning so i don't know what kind of data you're looking for. But from what I've heard in the industry, it's been very difficult to find live data feeds for League of legends, especially in China since the organisation running the tournaments over there are apparently not selling any live feeds to betting companies, often leading to latency issues and poor trading on the bookmaker's side. It's usually an esports trader manually adjusting odds while watching the stream haha. Or no live betting offered.

From what I could find, someone has already attempted to build a model here: (includes a link to a dataset, under downloads &amp; tools) https://www.quantumsportssolutions.com/blogs/league-of-legends/a-predictive-model-of-league-of-legends-game-outcomes
>
> **u/lequanghai** (2 pts): Where do you get data for esports? I mostly play and follow League of legends but cant find any complete dataset or source to perform analysis &amp; live betting.
>
> **u/Davidweb1337** (2 pts): E-sports is quite inefficient actually. It has only really started ramping up in the past few years but is still dwarfed by most traditional sports so bookmakers don't really invest as much into R&amp;D for it. You're very likely to find stale prices/lines here, but also very low betting limits.
>
> **u/bananarepubliccat** (2 pts): Yes,  most of the things you mention perform pretty poorly in reality.

Rolling window methods aren't that useful. You want to use season data with possibly priors from the previous season. Again, it is how information gets incorporated. With filter models, the update cycle is capturing all the right information...with rolling windows, you are getting some approximation of skill using unimportant information (against weak opponents, very old matches, etc.). You can weight more recent matches but it still won't beat ELO.

Btw, I didn't make this totally clear in my previous comment: the reason why these sports are hard to model is because the data is adversarial. The information comes from interactions between two teams, it is not only team skill but opponent skill that matters. This is particularly bad in football because you can have teams that win by doing things that would cause other teams to lose (this is less common in other invasion sports where there is usually a dominant strategy)...for example, if you have a model based on possession, teams that counter-attack will be rated poorly...and even then, that counter-attack strategy may only work against certain kinds of teams. And then you have a difference between offensive and defensive strategies: for example, Newcastle always used to outperform vs good teams because they were so defensively solid, but lost it whenever they had to attack the other team. It is very tricky. So an ELO model that has far less data will outperform because the ratings and difference of ratings capture the maximum amount of information.

If you are able to use some non-parametric grouping and then incorporate that into your rating then I think you would be able to produce a more traditional ML model that works (i.e. this team is a counterattack team against an attacking team so we expect X fast breaks, and they got X+5 so we increase their rating)...but even then, I still think the update cycle of filter models like ELO is very effe [...]
>
> **u/king-chungus** (2 pts): Don’t do deep learning, but I definitely think log regression, SVMs, etc… can be viable
>
> **u/ProdigyManlet** (2 pts): Thanks for the extremely detailed reply, this is absolutely awesome and is riddled with great info that answers a whole bunch of my questions (and some I hadn't even thought of yet).

By classification and traditional machine learning I'm referring to things like logistic regression, decision trees/random forest, support vector machines, etc. Basically traditional machine learning is non-deep learning methods. I definitely think Deep Learning would perform pretty poorly in most betting algos given the small data quantities.

In terms of data, I was using a rolling window (e.g. N games like you mentioned) that rolled across prior seasons to avoid the issue of say if N = 20, but we're at match 5 then there's only 4 data points. Obviously a lot changes between seasons which is not accounted for, but I was hoping to factor in information that captured these changes later on (i.e. manager changes/metrics and some form of player metrics). The Brier score looks good, and I like the idea of the ELO approach as it's much more manageable, simple and looks like it will be less reliant on across-season data; will look into all of these.

I had a feeling that the bigger markets will be more difficult. I will still try to get my basic model framework up and running using EPL, and then switch to some local leagues in my own country (looks like I can get the same data in basically the same format so should be an easy switch). I wanted to stick with a sport I have good domain knowledge in as I want to keep it interesting as a hobby while reviewing my classical statistics knowledge (I'm experienced in Deep Learning and Traditional ML, but it's been a while since I went back to the basics of distributions). However, I'll definitely take the suggestion onboard and look at some more obscure markets on the side. I was thinking of E-Sports but I would assume that might be quite efficient too.
>
> **u/TraptInaCommentFctry** (1 pts): &gt;you only update when you see something unexpected, the whole measure is weighted against peers

could you clarify what you mean by this?
>
> **u/bananarepubliccat** (1 pts): That isn't what I said.

I have used data that costs $100k+ annually, the features don't matter if you start from the wrong place (I explained this above, if you are seeing similar predictive power from ELO as ML then you have gone very wrong because ML, as most people are doing it, doesn't work...tbf, most people don't do ELO right either but that isn't a problem with the model). This varies by sport but the OP asked about soccer.

Using ELO as a feature is a basic error (and again, you are missing the point massively). ELO is just a filter, so you can use your ML model as an input to ELO: it is just a map from joint distribution of skill to prediction for a feature, so you can use ML as an input to ELO (I wouldn't advise building a mixture with ELO either, that is a very bad idea practically for soccer because of lineup changes).

How you do this is more complex but the key is that you are modelling a joint probability, that is where the power comes from. What OP will have tried is: X feature over N games or something similar, these models don't work (you can modify features, but it still won't get close). You can get them into a joint probability but, again, the problem is that they don't represent information correctly (again, this is obvious when you think carefully about what you are actually modelling...most people, inadvertently, end up with a single distribution for the average team...this works particularly poorly in soccer where there is no strategic equilibrium i.e. the meaning of features varies hugely based on the team).
>
> **u/MathMod3ler** (1 pts): Thanks for clarifying the original comment. Respectfully, I disagree that traditional ML is incapable of handling that amount of information. I think it comes down to having good features. Although, in practice I prefer using several ELO models as features in my ML models. So I definitely like the information ELO captures.
>
> **u/MathMod3ler** (1 pts): I disagree with a lot of this thread. Although, I think reasonable minds can disagree on this sort of stuff. I would say a couple things to take your modelling to the next level:

1)Stack uncorrelated models.
2) Use the betting market as a starting point for some of your models. The betting market is already a damn good model. Build on top of it, it already takes into account many of the basic features (probably including Poisson Distribution of goals). 
3) Come up with different targets. Ex: Win-Loss Binary and Difference in goals (they both tell you the betting outcome but the computer will look at them very differently).
4) Have way bigger test-validation sets than the normal rules of thumb. Finding patterns is easy...finding persistent patterns is hard.

My two cents, classification is fine. Just really do a lot of safe-guards and validation.
>

---

### [From Simple Models to Market Analysis: Is It Even Worth It?](https://reddit.com/r/algobetting/comments/1i7c0ma/from_simple_models_to_market_analysis_is_it_even/)
**Author**: u/National-Yogurt7021 | **Score**: 4 | **Comments**: 5 | **Date**: 2025-01-22

Some time ago, I started collecting historical data from football leagues and built a simple Python script. The script searches for teams in future matches based on specific criteria and finds teams with similar characteristics in the historical data. From a larger sample of the identified matches, it derives win probabilities and odds. I initially tested it with just one criterion, namely the average points per game. In the backtest, this resulted in a -12% yield, which didn’t surprise me, as it was extremely rudimentary. In that sense, it was amusingly a good contrarian indicator, so I tested a betting strategy based purely on randomness in the backtest. Even that performed better with a yield of -8%, lol.

I then planned to implement additional metrics to refine the model but decided instead to test the model provided by the site [xgscore.io](http://xgscore.io) by creating a Blogabet account. The reason was that I thought the approach used by the site seemed very sophisticated, and I probably wouldn’t be able to do better. On Blogabet, after 416 bets using their odds, I am currently at a yield of -7%. The sample size isn’t that large yet, but I find it hard to believe that it will improve significantly over time. The average odds are 2.318 (43%), with a win rate of 42%.

As of now, this would imply that the market odds (all bets placed on Pinnacle) pretty much reflect the actual win probabilities. This raises the question of whether it’s even worth pursuing such a project further, given how efficient the market seems to be. Respect to everyone who has managed to build a profitable model in these markets.

---

### [What sample size is significant?](https://reddit.com/r/algobetting/comments/18oltok/what_sample_size_is_significant/)
**Author**: u/verrts_ | **Score**: 3 | **Comments**: 9 | **Date**: 2023-12-22

I was doing backtests on +600 games. Although there is no look-ahead bias in my backtest, the results look a bit too good to be true:

* Sharpe ratio: 3.12
* Win rate: 46.5%
* Average ROI per won bet: 152% (edit for clarification: On average for every $1 won bet I get $2.52 in total. $1.52 is the profit).
* Risking 5% of the account balance per bet (initial balance: $1000) would yield at the end $55,000
* Biggest losing streak: 7
* Biggest drawdown: 36%

What do you think? Is it realistic? Is my sample size good enough to rely on this backtest?

---

### [the-odds-api for historical live odds reliable?](https://reddit.com/r/algobetting/comments/1kb4htn/theoddsapi_for_historical_live_odds_reliable/)
**Author**: u/[deleted] | **Score**: 2 | **Comments**: 6 | **Date**: 2025-04-30

---

### [Anyone know the status of MySportsFeeds.com?](https://reddit.com/r/algobetting/comments/105q4et/anyone_know_the_status_of_mysportsfeedscom/)
**Author**: u/postrema19 | **Score**: 2 | **Comments**: 4 | **Date**: 2023-01-07

Hi All.  Long time lurker/first time poster.  I have a background as software developer and am very interested in this space, but am finding it difficult locating a good source of historical data and/or feeds.

I  recently stumbled across what looked to be a promising API provider at [MySportsFeeds.com](https://MySportsFeeds.com), but have found them to be unresponsive.   The API and data modeling seem to be pretty mature and well organized, but I recently found that it is not returning data for NCAAM basketball, so I'm beginning to wonder if this site is now defunct.

Does anyone have any insight into the status of this provider?  If not, any recommendations in terms of other providers in this area would be well appreciated.  I am primarily interested in data for the "big four" of the US (NFL, MLB, NBA and NHL) as well as college basketball data.

Any help or direction is greatly appreciated!

---

### [Closing lines from yesterday??](https://reddit.com/r/algobetting/comments/1fpzudx/closing_lines_from_yesterday/)
**Author**: u/Old-Pie-9913 | **Score**: 2 | **Comments**: 3 | **Date**: 2024-09-26

Yo! Does anyone know where you can see yesterday's closing lines across sharp books? Pinny, Cris, Circa, etc.? I'm able to find main markets but am looking for props. So far no luck...anyone know where I can find historical prop lines? THANKS!

---

### [MLB Predict Relief Pitchers](https://reddit.com/r/algobetting/comments/1eadw7c/mlb_predict_relief_pitchers/)
**Author**: u/pipicks | **Score**: 2 | **Comments**: 5 | **Date**: 2024-07-23

I've created an MLB model which is currently seeing success in betting first 5 innings totals/spreads (relatively low sample size, but have been getting good clv so far). I want to extend this model to full games. The model is heavily reliant on the individual players in a lineup, so, currently the rotowire projected starting lineups are being used. 

Now I have ideas on how to model when the pitcher swap will happen, but I'm looking for suggestions on predicting the relief pitcher(s) that come on. My current thoughts are to look at past starts for the starting pitcher and obtaining a categorical distribution of possible (active) relief pitchers. I'm not a huge baseball fan so I don't know how naive this is. I appreciate any input.

---

### [Best way to use past XG data as a model feature for pre-match betting?](https://reddit.com/r/algobetting/comments/x4xgs3/best_way_to_use_past_xg_data_as_a_model_feature/)
**Author**: u/Bhagafat | **Score**: 1 | **Comments**: 5 | **Date**: 2022-09-03

If I have data sets such as from Understat which include XG, I can create a model off the back of this to predict things like final score, o2.5 yes/no, etc. for each match and backtest this. 

However without some kind of feature engineering for XG so that we have these features available to us before each game (e.g. avg XG past 6 games, etc.) this model would be useless for pre-match betting, because of course I don't know what the XG stats of a match will be until it happens.

I see a lot of people blindly resort to using Poisson probabilities, taking lambda to be the XG mean over x amount of games (inc. maybe some home/away weighting), but as accurate as Poisson can be it of course has its downfalls. I'd be interested to see if anyone has done some investigation into how to produce the best "pre-match statistics" involving XG. Has anybody got any links/reports/videos/etc. with some kind of discussion on best practices for feature engineering here?

Cheers

---

### [Model Evaluation](https://reddit.com/r/algobetting/comments/1fzzp9e/model_evaluation/)
**Author**: u/usmanirale | **Score**: 1 | **Comments**: 16 | **Date**: 2024-10-09

I am backtesting a model, and after backtesting for seven seasons, I got the following result: I start each season with a 1000-dollar bankroll, using the Kelly criterion and a max stake of 2% of the bankroll. I want to know if this outcome is inline with a winning model.



1. Win Rate:

2024: 60.32%

2023: 75.36%

2022: 42.67%

2021: 37.50%

2019: 50.56%

2018: 55.32%

2017: 52.63%



Average win rate: 53.48%



2. ROI (Return on Investment):

2024: 51.77%

2023: 117.78%

2022: -21.42%

2021: 0.05%

2019: 70.33%

2018: 26.64%

2017: 26.32%



Average ROI: 38.78%



3. Average Value Percentage:

2024: 28.72%

2023: 25.80%

2022: 34.19%

2021: 45.74%

2019: 29.48%

2018: 40.10%

2017: 29.11%



Average value percentage: 33.31%



4. Log Loss (Predictive vs Historical):

2024: 0.4643 vs 0.4765

2023: 0.5018 vs 0.5488

2022: 0.5197 vs 0.4999

2021: 0.4829 vs 0.4896

2019: 0.6484 vs 0.6531

2018: 0.5355 vs 0.5650

2017: 0.5827 vs 0.5828



Average Predictive Log Loss: 0.5336

Average Historical Log Loss: 0.5451



5. Profit/Loss:

2024: +$517.68

2023: +$1,177.78

2022: -$214.17

2021: +$0.54

2019: +$703.31

2018: +$266.43

2017: +$263.24



Total profit over 7 seasons years: $2,714.81

---

## NBA / Basketball

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [A tool for analysing odds](https://reddit.com/r/algobetting/comments/yd86kl/a_tool_for_analysing_odds/)
**Author**: u/_rbp_ | **Score**: 13 | **Comments**: 8 | **Date**: 2022-10-25

I have created an application for analysing odds – [www.rationalbets.com](https://www.rationalbets.com). It allows to identify profitable sports bets using the concept of expected value. I would be very grateful if you could check it's handy and provide feedback.

All you have to do to use it is:

· Choose an event from the sidebar or add a custom one.

· Set the probabilities of the event outcomes to your best knowledge using intuitive sliders.

Based on the probability distribution you specify, the tool will calculate the expected profits of your picks.

The tool is regularly updated with odds for football, NFL, baseball, and basketball. There is also an article section on maths in gambling.

www.rationalbets.com

**Top Comments:**

> **u/consolationgoal** (5 pts): It looks like you are using straight probabilities from the bookmaker's odds, meaning that the equation is 1/odds = probability. Right?

That means your probabilities include the bookmaker's margin, which in turn shows the expected net to win as zero. In reality, given bookmaker margins, the expected net to win should start out as negative. After all, that's how they make their money. Only by adjusting the probabilities should you be able to move the expected profit to zero or positive. 

In the Leicester City - Man City example, Pinnacle odds are 10.09 x 6.20 x 1.30. That means the bookmaker margin is 2.9% 

(1/10.09) + (1/6.20) + (1/1.30) = 1.029

So unless a person moves the sliders, it the net expected profit from a 10 euro bet should be -0.29 right?
>
> **u/_rbp_** (3 pts): I think there are a few good arguments against parlays:

1. As good as you might be at predicting events, you can't always get everything right. Losing parlays happens often, as the probability of winning decreases exponentially. For example let's say you place 5 bets, each one with a 90% chance winning (as sure as you can be of an outcome in most cases). The chance of winning a parlay is only 90%\^5 = 59%.
2. Parlays are bets with large odds, but a small probability of a payout. Such types of bets drastically increase the variance of your winnings. In other words, you have a larger chance of winning big, but also a larger chance of loosing big. I actually have a nice simulation of that in my [article on variance](https://www.rationalbets.com/articles/#variance).
3. There's one argument I don't think is necessary true, but probably is very often true - when placing a bet, you are paying the bookmaker his margin. The more bets you place in a parlay, the more this margin will increase (as it multiplies across all your picks).

These arguments aren't just theory - I don't believe any professional bettor would do parlays for the above reasons (unless from time to time for fun).
>
> **u/consolationgoal** (3 pts): Thanks for the explanation. You should check out the below paper, which gives great detail on how best to remove the bookmaker margin (including formulas). As you said, there is no exact certainty on how a given bookmaker does it, but the testing in the below paper makes clear the best option for the public to try to remove the bookmaker margin.

[https://www.football-data.co.uk/The\_Wisdom\_of\_the\_Crowd\_updated.pdf](https://www.football-data.co.uk/The_Wisdom_of_the_Crowd_updated.pdf)

I totally understand the desire to maybe not go crazy on precision, but professional sports bettors are often surviving on 1% edges (especially in the major sports like you've got on this tool), so I think precision is key.

More broadly, who is the target market for the tool? I feel like recreational bettors are unlikely to have a probability (even a reasonable range, frankly) for their desired bet, so they might not be able to take advantage of the tool. They are likely going to just line-shop, which your tool does help with but there are other more established options out there for that (Betstamp, etc). 

Originators - i.e. handicappers who create their own probabilities for an event - will be able to fairly easily determine their projected edge.

I don't really do parlays so I didn't check out that part of things, but it's true those probabilities are less well understood generally so that might be something that draws people's attention.

Looks like a lot of work went into the tool. Great job getting to this place.
>
> **u/Available_Remove452** (3 pts): I'm interested in trying this, thank you.
>
> **u/Loyalty4life187** (2 pts): How bout the guys on the book or the tube that wants to tell you how ya become a millionaire 🤣 and they ain’t even one..
>
> **u/_rbp_** (2 pts): I never really analysed picks, but my intuition is in most cases it might be the same as with "investment gurus" selling books - for most it goes, if they were really that good at predicting what will happen, they would simply be making money this way and not seeking a fee for sharing their wisdom.
>
> **u/Loyalty4life187** (2 pts): Sites because this year or maybe I’ve never noticed cause I never paid it no mind just used my own intuition is that what the experts tell people to pick I found that I’m not good at math but say for example SportsLine other night shot every pick wrong.  I mean right now it’s something to do ya know so I been doing basketball n football
>
> **u/Loyalty4life187** (2 pts): Yea I’m lost wish I knew what the heck was talking bout, I do parlays a lot n be off by like 1 game n what not.
>
> **u/_rbp_** (2 pts): Thank you! I hope for some feedback. The concept makes sense to me and works on my devices, and I hope to confirm it does for others too.
>
> **u/Loyalty4life187** (1 pts): I clicked on article what part/ NeverMind I got it
>

---

### [Making NBA models](https://reddit.com/r/algobetting/comments/1e0ptxd/making_nba_models/)
**Author**: u/makingstuff237 | **Score**: 9 | **Comments**: 16 | **Date**: 2024-07-11

Hi everyone, I've downloaded every box score, quarter box score and even play by plays for every nba game and then I scraped all of the info into an sql database. I've made a few VERY basic models and would like ideas on what to do next.

My most advanced model (still super basic) takes two teams and a date (usually automated by the days schedule so it does it automatically) and spits out predicted stats for each player. I get the prediction by taking a look at stats over the past 5, 10, 20 games as well as full season, but I only look at the home or road games depending on the team. So if it's BOS at LAL I would look at Boston's past 5, 10, 20 and any game played on the road and vice versa for LA. For each of those splits (5, 10, 20, all) I get the players average stats, the opposing teams average defensive stats and the nba average defensive stats for those spans for each quarter, 1-4. I then compare the nba average defensive stats (on the road or at home, to match the team I'm looking at) to the teams defensive stats and make it a percentage. So let's say NBA average on the road allows 10 fg3a's in the first quarter but let's say Boston allows 9.5 fg3a's in the first over the same split, then my algorithm would have Boston's fg3a percentage at 95%, then I take the players averages and multiply it by the percentage to get my estimate. I do this for every stat I can. 

The program then looks at the odds which I scrape from draft kings and then compares the bet to my predicted stat and gives a confidence rating which is not impressive, it's literally just comparing my prediction to the line and then giving a bonus multilier depending on it's value, so if I show a player having 9 rebounds and the line is set at 7.5 and the over is -140 then I have a difference of 120% and then I multiply that by how far away the value is from 0, the further negative the lower the multiplier. I don't 100% remember how I did this and can't look it up on this computer right now but suffice to say it's very lacking. I have it spit out the bets it thinks are best and usually it picks about 5-10 bets per day, of those it had a pretty high ROI but the model is so simple and it needs improvement. It has obvious flaws like not being able to know who is and who isn't playing in a game among I'm sure 10,000,000 other things.


This was started as just a fun project to teach me how to scrape websites and use mysql but I'd like to learn more. I don't know about betting strategies or EV betting or anything really, I'm just 100% self taught. Any advice on what to look into would be great. Also worth noting I've only utilized full game and quarter box score information, I have not done anything with my play by play table. I've also written some code so it can identify who is on the court at any time and shows all 10 players on the court for any play and combined it with the shots data available to get the x and y coordinates of any shot taken. Here's a screenshot of my altered pbp table: https://imgur.com/a/4BxHCXW (note that it cuts off and doesn't show all 10 players in the screen shot, they're all in the table, they just didn't all fit in the screenshot.

I also have a players table with everyone's names, hand, height, weight, dob, draft info, college info, etc. As mentioned, this started out as a project to teach me python and mysql.

Everything is sourced from basketball reference and draft kings, 100% free, if anyone would be willing to help me I might be willing to share my scraping scripts.

**Top Comments:**

> **u/LawyersGunsMoneyy** (3 pts): My thought process is that the implied odds based on the line is what you need to hit to be profitable. So if there’s a line that is listed at +100, you need to hit 50% to break even, regardless of whether the line has 1% juice or 20% juice
>
> **u/makingstuff237** (2 pts): Thank you so much for the tip, I'll check it out!
>
> **u/kicker3192** (2 pts): Yes, this. De-vigging the lines only serves if you're going to utilize the books' implied probability to calculate something within the model (i.e. your model is top down and you're going to use the books' odds as a variable).
>
> **u/ezgame6** (2 pts): you still bet on the vigged odds... what you're saying is if you want to estimate your true edge? I don't see how vig free odds affect your decision making
>
> **u/makingstuff237** (1 pts): Kind of. It was a ton of work and I'm not willing to share it for free. Nor do I have a place to host it
>
> **u/fuckosta** (1 pts): Hey would you mind if I could have a look at your dataset?
>
> **u/Foreign-Procedure-91** (1 pts): Hello. Apparently it's a very interesting job.
    Does your model take into account how the absence of a player affects other players?
    For example, if a player is absent, and his individual contribution will change little. But this could have a greater impact on the game of other players
>
> **u/NarwhalDesigner3755** (1 pts): NBA API doesn't have everything, I had to merge their data with another source that I had scraped to give me a more complete picture
>
> **u/Traditional_Soil5753** (1 pts): From my experience if you use the Kelly criterion formula you don't have to worry about "de-vigging". Sports books odds can also be viewed as "% of wager returned"...ie +200 odds is just 100% of your wager returned on a win. +300 odds is just 200% of wager returned....plug this into Kelly criterion formula for your bet size and your good to go....
>
> **u/DotSlashSports** (1 pts): No problem. I'd listen to some of the Spotify podcasts with the person who did DARKO. His name is Kosta. I'm sure you will get some good nuggets of info from them.
>

---

### [My attempt at a model to bet on NFL games](https://reddit.com/r/algobetting/comments/ggaz71/my_attempt_at_a_model_to_bet_on_nfl_games/)
**Author**: u/HamirTime | **Score**: 8 | **Comments**: 14 | **Date**: 2020-05-09

Hey guys, been lurking since this subreddit got created and knew I would be contributing to it once I got my model to an "acceptable" state to hopefully get further insight.

Gonna try to keep this as short as possible because alot of explaining happens in the Jupyter notebook, but here goes.

So basically I took a data mining course this last semester and the final project was to apply the concepts we learned in class to a real world scenario. While the NFL was in full swing, I was a frequent sports better and would really enjoy betting and watching the games. Data and modeling still seemed like such a complex topic to me, but I knew that eventually I would the subject either in class or on my own. After learning the data mining world, this in-class project was a perfect way to test what I had learned as well as try and use my skills to make some money.

SO with all that out of the way, the summation of the actual data and models is that I took game data from Kaggle (mainly used to pull the scores) and added full team rosters for both away and home teams (rosters scraped from another site). My thought was that since each team is composed of 52 players, that at the end of the day their performances (with the leadership of the head coach) is what determined the outcomes of the game. So to summarize, each of my records contained the home and away teams, current W-L records, and most relevant positions for both teams. I also decided to filter the data to only be within this millennia.

With this data I tried to use regression models to predict the score of the games. This score would then be compared with the vegas spread for that game so that the model could predict whether it should bet on the home team or the away team to cover the spread. This might not be a good practice, but I just decided to use every game from the 2000-2018 season to predict 2019 games as my model testing phase. I used the SVM Regressor algorithm (primarily because it was the only one that supported unbalanced data, which is obviously important since the more recent games should play a bigger factor) and an Artificial Neural Network because it's pretty easy to grasp and honestly doesn't require much thinking or work from me. Kinda also used it in case I was configuring the SVM wrong.

In summary, my results were slightly worse than I was expecting.  Both my models average out to about 52% accuracy and a mean squared error of around 195 when compared to the actual point values. Hence the main reason I am posting here: to get some help from more experienced data scientists.

I've decided to include my work here, both for more experienced people to critique and maybe for some less experienced people to learn. This project was, again, done as a school project so please excuse some of my markdown comments as they had to follow a format for the class. This is also done in Python primarily using scikit learn for all data modeling and pandas for pre-processing. I used VS Code as my IDE with the Microsoft Python plugin to view and edit Jupyter Notebooks.

I want to keep developing this in the future, at this point not even to make money but just because I think it's a cool concept. The thought of math being able to better predict as complex a game as football more accurately than almost anyone is crazy. Other than this model, I recently also purchased a Raspberry Pi (also being used for other side projects) to eventually automatically pull new game data for the model to predict.

Like I said above please feel free to critique, this was basically my first major python project and I had no experience with any of these libraries. Also don't usually post on Reddit so if my formatting sucks call me out on that too.

Thanks guys, hope this is a helpful post to keep the subreddit going.

Jupyter Notebook: http://www.filedropper.com/finalproject_2 (not sure how long the site will host the file TBH)

**Top Comments:**

> **u/15woodsjo** (4 pts): To piggy back off this answer, I would also throw in a suggestion of using a neural network and turning this into a binary classification problem.

In practicality this is a logistic regression model that you have more control over, and can potentially get a little bit better of a model out of the algorithm.

&amp;#x200B;

The reason I would suggest anything binary classification for this type of problem is you would want to be able to measure the % likelihood of one team vs. another covering the spread whilst the line moves. In essence, you can get more information by knowing that team A has a 60% likelihood of covering a (-9) line and team B has a 40% chance PLUS team A has a 55% likelihood of covering a (-10) line and team B has a 55% chance. Basically you want to be able to apply your model to a dynamic line to get what is hopefully a more accurate picture of a +EV game
>
> **u/KidMcC** (3 pts): Will respond more fully later, but one thing that jumps out at me is that you might want to explore using a GLM with Poisson distribution as opposed to something like SVMs for football scores. This allows you a better probability assignment to different outcomes. 

Basic googling should land you more stats-focused details on that.

As an aside, there are better ways to handle imbalanced data than using an SVM for assigning binary winner/loser status. SVMs rarely perform consistently better than some other such models, like Logistic Regression or Random Forest Classifiers. Looking into weighted logistic regression or sub-sampling to balance out data as opposed to picking a specific model family as a result.

&amp;#x200B;

Again, will respond more later, as it's an interesting problem. Also open to debate re: any of the above.
>
> **u/15woodsjo** (2 pts): That's fair, my background is in basketball where I suppose there is a larger sample size.
>
> **u/KidMcC** (2 pts): This is a very important distinction. "Binary classification" can be done at least two ways here.   
1) Linear model (of sorts) fit to predict the point difference (homeScore - awayScore). Again, GLM approach with Poisson Distribution is the most common choice for football for a reason, given how scoring is not linear with each point-accumulating event. The sign of the endogenous variable would then be indicating the "win" the same way a 1/0 would in your example. Here you can use size of the difference to indicate probability, to some degree.   
[https://www.sbo.net/strategy/football-prediction-model-poisson-distribution/](https://www.sbo.net/strategy/football-prediction-model-poisson-distribution/)

[https://www.pinnacle.com/en/betting-articles/Soccer/how-to-calculate-poisson-distribution/MD62MLXUMKMXZ6A8](https://www.pinnacle.com/en/betting-articles/Soccer/how-to-calculate-poisson-distribution/MD62MLXUMKMXZ6A8)

2) Ignore points and predict an actual binary variable indicating whether or not the home team won. What this modeling approach provides is a direct probability associated with each classification. This also requires a choice to be made of regularization, L1/L2 penalty if using Logistic Regression, etc.  


Predicting scores via regression, and then daisy-chaining that back into a spread comparison to then take advantage of error profiling, like you said, is quite indirect and will certainly introduce more bias and/or volatility than what it returns in accuracy.
>
> **u/KidMcC** (2 pts): If we are talking about predicting binary game outcome, then I'd be hesitant to go the route of neural network. By its very nature of scheduling and season construction, football doesn't offer a huge dataset of games to really draw from (compared to other sports). Especially if you aren't weighting games from the distant past fairly, one can find themselves with a high variance, over-parameterized model fit on too little an amount of data. All my opinion of course! 

I do think a thoughtful feature selection process fit to an XGB or RandomForest model might be more manageable given that gameplay data gets old fast. Exponential weighting can be your friend here, though, if you need to go way back, just make sure your offense-profiling is dynamic!
>
> **u/15woodsjo** (2 pts): You are implementing a binary decision based on your model but not using an algorithm that is trained using binary classification. Slight difference
>
> **u/HamirTime** (2 pts): Thanks for the insight, I will definitely look into GLMs and their applications. I'm more familiar with logistic regression, so I would probably err towards looking into that to better handle imbalanced data
>
> **u/HamirTime** (2 pts): I could be misunderstanding your suggestion, but I think I am currently already transforming this into a binary classification problem. After using regression to calculate the score, I compare it with the spread to calculate a 'class' variable (0 or 1). 0 meaning a bet should be placed on the away team and a 1 meaning a bet on the home team. I use these to also measure common metrics like accuracy, precision, and recall.

 The likelihood percentages was also something I wanted to implement by using the difference between the predicted score and the spread, but wanted to focus on improving the model before then
>
> **u/anxiousalpaca** (1 pts): You are right, i totally misread what is meant by daisy-chaining back (not an English native speaker)
>
> **u/KidMcC** (1 pts): The OP said nothing of features describing the relative defensive capability of either side of the ball. Without such features, I'd still say daisy-chaining yhat values for score back into a comparison is risky, as it leaves nothing in the model reflecting the fact that for one team's offense to have the opportunity to score, it generally requires that the other team does not have the same opportunity at the same time (save for pick-6s). Volatility would be unstable when you begin to use this approach with games where disparity between defensive capability on each side is substantial. At least, this is what I have found. Curious to hear more if this is still at odds with your experience.
>

---

### [Programmer looking to get started](https://reddit.com/r/algobetting/comments/1gaitzp/programmer_looking_to_get_started/)
**Author**: u/racerx1036 | **Score**: 5 | **Comments**: 4 | **Date**: 2024-10-23

I am a programmer by profession but want to get into algo betting. I work with PHP by way of trade, but have dabbled in python before would definitely need to learn some stuff there as I go though. Whats the best way to get started building an algo im thinking of starting with NBA stats since they seem to be relatively predictable and reliable. I figure doing Overall game stats would be easier to start than including player props like ppg etc but I do want those down the line. I want to as I learn more be able to build this into quite a complex model. What is a good starting point / places to research or watch, first kind of model to build etc. So for NBA what would be some principals to learn to build this model. Any tips appreciated. Thanks!

**Top Comments:**

> **u/Governmentmoney** (1 pts): There are many ways to do things, if you're going down the ML route you can get some ideas from here: [https://betfair-datascientists.github.io/modelling/howToModel/](https://betfair-datascientists.github.io/modelling/howToModel/)

Pretty basic stuff but it will give you a direction to move towards and experiment
>
> **u/__sharpsresearch__** (1 pts): nba_api is was faster than scraping. it will save you days.

pandas/sklearn/numpy should be all you need on the modeling front for the most part

decision trees are very common, our model that is currently running on our site is using a light gradient boosted tree
>
> **u/racerx1036** (1 pts): Thinking of just web scraping something and playing around with pandas and decision trees but not really sure what to do there so I’ll have to do some researching. But yeah like u say to start simple but when I’m ready for more what direction do I head?
>
> **u/__sharpsresearch__** (1 pts): good picks on nba, high level team stats btw.


nba_api is great. join their slack.

initially, make a db, grab everything from ~2008-2010 and throw it in a team, player, match, boxscore table. or something similar so you can fuck around and not get rate limited.
>

---

### [How useful is something like this](https://reddit.com/r/algobetting/comments/1k662a4/how_useful_is_something_like_this/)
**Author**: u/Forsaken-Hearing3540 | **Score**: 4 | **Comments**: 17 | **Date**: 2025-04-23

www.playerprobabilities.com

I’ve been working on a machine learning model to predict NBA player props — specifically points, assists, and rebounds. Originally, I used linear regression (with Lasso for feature selection) and rolling averages to predict raw values. That alone gave me around 57  - 70% accuracy on some given days, this is for 68+ players on game days.

Now I’ve taken it a step further:
I treat the regression prediction as a mean,
Calculate a confidence interval using a z-score (95% confidence),
Run Monte Carlo simulations to estimate the distribution of outcomes,
Then compute the probability a player hits the over/under line.

Also a second reason why I am here ,can you guys share any tips on how you guys account for lineup changes and how it affects what a player is going to score. I have really been struggling with that aspect of things.l

---

### [NBA player prop stats scraping](https://reddit.com/r/algobetting/comments/13w2no6/nba_player_prop_stats_scraping/)
**Author**: u/fiachrah98 | **Score**: 4 | **Comments**: 4 | **Date**: 2023-05-30

Hi,
I’ve been running a player prop betting system for NBA since start of conference finals but it consists of me going to different websites and copying and pasting info every day.

These are the website I need a way of extracting the table from into a google sheet.

Any help is appreciated.

https://www.nba.com/stats/players/traditional?PerMode=Totals&amp;LastNGames=5

https://www.lineups.com/nba/nba-player-minutes-per-game

System after conference finals:

Bets: 121
Profit: 22.71u
ROI: 14.6%

---

### [Beating books on NBA Props](https://reddit.com/r/algobetting/comments/1kf2o9j/beating_books_on_nba_props/)
**Author**: u/Consistent_Buy625 | **Score**: 3 | **Comments**: 1 | **Date**: 2025-05-05

I’ve been testing a few different models against NBA player props (points, assist, rebounds) to see how they compare to sportsbooks. I’ve been using things like the way back machine on rotowire to obtain large amounts of previous props at once. I’m wondering if it’s worth also testing across playoff seasons to see if there is any variance due to playoff performance from players being different than the regular season, and also how much of an edge I would need in order to break even/become profitable

---

### [How sharp really is FanDuel on NBA props?](https://reddit.com/r/algobetting/comments/1keycjh/how_sharp_really_is_fanduel_on_nba_props/)
**Author**: u/jcmmania | **Score**: 3 | **Comments**: 4 | **Date**: 2025-05-05

I have heard through the grapevine multiple times that FanDuel is sharp on NBA player props. For this reason, as a top-down bettor I’ve been avoiding betting NBA player props into Fanduel, even when they diverge significantly from the rest of the market including actually sharp books like Pinnacle. Am I overrating Fanduel in this regard? Also, how does time from tip-off play into this (i.e. does Pinnacle’s edge over Fanduel increase as they take more sharp action on a given game)?

---

### [NBA scores predicting](https://reddit.com/r/algobetting/comments/1flxcib/nba_scores_predicting/)
**Author**: u/FireDragonRider | **Score**: 3 | **Comments**: 26 | **Date**: 2024-09-21

Yesterday I finally invented a way to predict NBA games. Maybe 🤔 

I use NBA API, calculate some averages, then I ask GPT about them, then create some embedding vectors, then logistic regression. In the end I have probabilities of a team scoring more than each possible score plus minus 20 from the real score. So the first 20 should have a higher probability of "more", the second 20 should have a higher probability of "less". 

What do you think is the best way to test this algorithm? What metrics should I use to test it well and either against bookmaker predictions or at least against real scores, comparing the average accuracy to bookmakers?

---

### [Underdog NFL +EV Record by Week](https://reddit.com/r/algobetting/comments/1iolda6/underdog_nfl_ev_record_by_week/)
**Author**: u/FavoredProps | **Score**: 2 | **Comments**: 0 | **Date**: 2025-02-13

**What’s up! We graphed the hit rate for props identified as +EV on the Underdog DFS site for the 2024 NFL Regular Season.** 



**Approach:**

⁃    Included standard-payout props with -125 or better average odds from 4+ sportsbooks

⁃    Props with line changes were considered separate props

⁃    Since we had 15 minute snapshots of data, the last occurrence of a prop was used to prevent duplicates



The **overall hit rate for the regular season was 54.6%** over 3601 props that were included in the approach above. For context, the **breakeven hit rate for each pick in a 6-leg flex parlay is 53.8%.** 



**Also, “Under” +EV props are more accurate and made up just 40% of the total count.**

⁃    Over: 53.9%

⁃    Under: 55.7%



It seems like blindly tailing +EV plays this season would’ve earned a small profit. To help get those numbers up, we made a Free Player Prop Tool [https://www.favoredprops.com/dfs/nba](https://www.favoredprops.com/dfs/nba) to research more data points like defensive rankings, line movement, and hit-rate in various situations



**Let us know if you’d like to see more content like this!**

https://preview.redd.it/553omucibxie1.jpg?width=1440&amp;format=pjpg&amp;auto=webp&amp;s=858e96555ef6bd79da1384c5d62ee3dc61b38483

---

### [Anyone know the status of MySportsFeeds.com?](https://reddit.com/r/algobetting/comments/105q4et/anyone_know_the_status_of_mysportsfeedscom/)
**Author**: u/postrema19 | **Score**: 2 | **Comments**: 4 | **Date**: 2023-01-07

Hi All.  Long time lurker/first time poster.  I have a background as software developer and am very interested in this space, but am finding it difficult locating a good source of historical data and/or feeds.

I  recently stumbled across what looked to be a promising API provider at [MySportsFeeds.com](https://MySportsFeeds.com), but have found them to be unresponsive.   The API and data modeling seem to be pretty mature and well organized, but I recently found that it is not returning data for NCAAM basketball, so I'm beginning to wonder if this site is now defunct.

Does anyone have any insight into the status of this provider?  If not, any recommendations in terms of other providers in this area would be well appreciated.  I am primarily interested in data for the "big four" of the US (NFL, MLB, NBA and NHL) as well as college basketball data.

Any help or direction is greatly appreciated!

---

### [Feedback wanted for a ML prediction model](https://reddit.com/r/algobetting/comments/1jrd44c/feedback_wanted_for_a_ml_prediction_model/)
**Author**: u/Jp46810557 | **Score**: 1 | **Comments**: 7 | **Date**: 2025-04-04

A few of us have been working on a machine learning model to predict NBA game outcomes (Moneyline, Spread, O/U). We're in the early stages and would love to get some feedback from the community on its potential and areas for improvement.

Our model considers factors like team performance, recent game history, and some contextual elements. We're particularly interested in hearing what you think are the most important indicators for predicting NBA games accurately.

If anyone is interested in seeing some of the model's daily predictions and providing feedback, feel free to DM me and I can share more info. We're really focused on learning and making this a useful tool.

---

## Expected Value & Edge Detection

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [A tool for analysing odds](https://reddit.com/r/algobetting/comments/yd86kl/a_tool_for_analysing_odds/)
**Author**: u/_rbp_ | **Score**: 13 | **Comments**: 8 | **Date**: 2022-10-25

I have created an application for analysing odds – [www.rationalbets.com](https://www.rationalbets.com). It allows to identify profitable sports bets using the concept of expected value. I would be very grateful if you could check it's handy and provide feedback.

All you have to do to use it is:

· Choose an event from the sidebar or add a custom one.

· Set the probabilities of the event outcomes to your best knowledge using intuitive sliders.

Based on the probability distribution you specify, the tool will calculate the expected profits of your picks.

The tool is regularly updated with odds for football, NFL, baseball, and basketball. There is also an article section on maths in gambling.

www.rationalbets.com

**Top Comments:**

> **u/consolationgoal** (5 pts): It looks like you are using straight probabilities from the bookmaker's odds, meaning that the equation is 1/odds = probability. Right?

That means your probabilities include the bookmaker's margin, which in turn shows the expected net to win as zero. In reality, given bookmaker margins, the expected net to win should start out as negative. After all, that's how they make their money. Only by adjusting the probabilities should you be able to move the expected profit to zero or positive. 

In the Leicester City - Man City example, Pinnacle odds are 10.09 x 6.20 x 1.30. That means the bookmaker margin is 2.9% 

(1/10.09) + (1/6.20) + (1/1.30) = 1.029

So unless a person moves the sliders, it the net expected profit from a 10 euro bet should be -0.29 right?
>
> **u/_rbp_** (3 pts): I think there are a few good arguments against parlays:

1. As good as you might be at predicting events, you can't always get everything right. Losing parlays happens often, as the probability of winning decreases exponentially. For example let's say you place 5 bets, each one with a 90% chance winning (as sure as you can be of an outcome in most cases). The chance of winning a parlay is only 90%\^5 = 59%.
2. Parlays are bets with large odds, but a small probability of a payout. Such types of bets drastically increase the variance of your winnings. In other words, you have a larger chance of winning big, but also a larger chance of loosing big. I actually have a nice simulation of that in my [article on variance](https://www.rationalbets.com/articles/#variance).
3. There's one argument I don't think is necessary true, but probably is very often true - when placing a bet, you are paying the bookmaker his margin. The more bets you place in a parlay, the more this margin will increase (as it multiplies across all your picks).

These arguments aren't just theory - I don't believe any professional bettor would do parlays for the above reasons (unless from time to time for fun).
>
> **u/consolationgoal** (3 pts): Thanks for the explanation. You should check out the below paper, which gives great detail on how best to remove the bookmaker margin (including formulas). As you said, there is no exact certainty on how a given bookmaker does it, but the testing in the below paper makes clear the best option for the public to try to remove the bookmaker margin.

[https://www.football-data.co.uk/The\_Wisdom\_of\_the\_Crowd\_updated.pdf](https://www.football-data.co.uk/The_Wisdom_of_the_Crowd_updated.pdf)

I totally understand the desire to maybe not go crazy on precision, but professional sports bettors are often surviving on 1% edges (especially in the major sports like you've got on this tool), so I think precision is key.

More broadly, who is the target market for the tool? I feel like recreational bettors are unlikely to have a probability (even a reasonable range, frankly) for their desired bet, so they might not be able to take advantage of the tool. They are likely going to just line-shop, which your tool does help with but there are other more established options out there for that (Betstamp, etc). 

Originators - i.e. handicappers who create their own probabilities for an event - will be able to fairly easily determine their projected edge.

I don't really do parlays so I didn't check out that part of things, but it's true those probabilities are less well understood generally so that might be something that draws people's attention.

Looks like a lot of work went into the tool. Great job getting to this place.
>
> **u/Available_Remove452** (3 pts): I'm interested in trying this, thank you.
>
> **u/Loyalty4life187** (2 pts): How bout the guys on the book or the tube that wants to tell you how ya become a millionaire 🤣 and they ain’t even one..
>
> **u/_rbp_** (2 pts): I never really analysed picks, but my intuition is in most cases it might be the same as with "investment gurus" selling books - for most it goes, if they were really that good at predicting what will happen, they would simply be making money this way and not seeking a fee for sharing their wisdom.
>
> **u/Loyalty4life187** (2 pts): Sites because this year or maybe I’ve never noticed cause I never paid it no mind just used my own intuition is that what the experts tell people to pick I found that I’m not good at math but say for example SportsLine other night shot every pick wrong.  I mean right now it’s something to do ya know so I been doing basketball n football
>
> **u/Loyalty4life187** (2 pts): Yea I’m lost wish I knew what the heck was talking bout, I do parlays a lot n be off by like 1 game n what not.
>
> **u/_rbp_** (2 pts): Thank you! I hope for some feedback. The concept makes sense to me and works on my devices, and I hope to confirm it does for others too.
>
> **u/Loyalty4life187** (1 pts): I clicked on article what part/ NeverMind I got it
>

---

### [Making NBA models](https://reddit.com/r/algobetting/comments/1e0ptxd/making_nba_models/)
**Author**: u/makingstuff237 | **Score**: 9 | **Comments**: 16 | **Date**: 2024-07-11

Hi everyone, I've downloaded every box score, quarter box score and even play by plays for every nba game and then I scraped all of the info into an sql database. I've made a few VERY basic models and would like ideas on what to do next.

My most advanced model (still super basic) takes two teams and a date (usually automated by the days schedule so it does it automatically) and spits out predicted stats for each player. I get the prediction by taking a look at stats over the past 5, 10, 20 games as well as full season, but I only look at the home or road games depending on the team. So if it's BOS at LAL I would look at Boston's past 5, 10, 20 and any game played on the road and vice versa for LA. For each of those splits (5, 10, 20, all) I get the players average stats, the opposing teams average defensive stats and the nba average defensive stats for those spans for each quarter, 1-4. I then compare the nba average defensive stats (on the road or at home, to match the team I'm looking at) to the teams defensive stats and make it a percentage. So let's say NBA average on the road allows 10 fg3a's in the first quarter but let's say Boston allows 9.5 fg3a's in the first over the same split, then my algorithm would have Boston's fg3a percentage at 95%, then I take the players averages and multiply it by the percentage to get my estimate. I do this for every stat I can. 

The program then looks at the odds which I scrape from draft kings and then compares the bet to my predicted stat and gives a confidence rating which is not impressive, it's literally just comparing my prediction to the line and then giving a bonus multilier depending on it's value, so if I show a player having 9 rebounds and the line is set at 7.5 and the over is -140 then I have a difference of 120% and then I multiply that by how far away the value is from 0, the further negative the lower the multiplier. I don't 100% remember how I did this and can't look it up on this computer right now but suffice to say it's very lacking. I have it spit out the bets it thinks are best and usually it picks about 5-10 bets per day, of those it had a pretty high ROI but the model is so simple and it needs improvement. It has obvious flaws like not being able to know who is and who isn't playing in a game among I'm sure 10,000,000 other things.


This was started as just a fun project to teach me how to scrape websites and use mysql but I'd like to learn more. I don't know about betting strategies or EV betting or anything really, I'm just 100% self taught. Any advice on what to look into would be great. Also worth noting I've only utilized full game and quarter box score information, I have not done anything with my play by play table. I've also written some code so it can identify who is on the court at any time and shows all 10 players on the court for any play and combined it with the shots data available to get the x and y coordinates of any shot taken. Here's a screenshot of my altered pbp table: https://imgur.com/a/4BxHCXW (note that it cuts off and doesn't show all 10 players in the screen shot, they're all in the table, they just didn't all fit in the screenshot.

I also have a players table with everyone's names, hand, height, weight, dob, draft info, college info, etc. As mentioned, this started out as a project to teach me python and mysql.

Everything is sourced from basketball reference and draft kings, 100% free, if anyone would be willing to help me I might be willing to share my scraping scripts.

**Top Comments:**

> **u/LawyersGunsMoneyy** (3 pts): My thought process is that the implied odds based on the line is what you need to hit to be profitable. So if there’s a line that is listed at +100, you need to hit 50% to break even, regardless of whether the line has 1% juice or 20% juice
>
> **u/makingstuff237** (2 pts): Thank you so much for the tip, I'll check it out!
>
> **u/kicker3192** (2 pts): Yes, this. De-vigging the lines only serves if you're going to utilize the books' implied probability to calculate something within the model (i.e. your model is top down and you're going to use the books' odds as a variable).
>
> **u/ezgame6** (2 pts): you still bet on the vigged odds... what you're saying is if you want to estimate your true edge? I don't see how vig free odds affect your decision making
>
> **u/makingstuff237** (1 pts): Kind of. It was a ton of work and I'm not willing to share it for free. Nor do I have a place to host it
>
> **u/fuckosta** (1 pts): Hey would you mind if I could have a look at your dataset?
>
> **u/Foreign-Procedure-91** (1 pts): Hello. Apparently it's a very interesting job.
    Does your model take into account how the absence of a player affects other players?
    For example, if a player is absent, and his individual contribution will change little. But this could have a greater impact on the game of other players
>
> **u/NarwhalDesigner3755** (1 pts): NBA API doesn't have everything, I had to merge their data with another source that I had scraped to give me a more complete picture
>
> **u/Traditional_Soil5753** (1 pts): From my experience if you use the Kelly criterion formula you don't have to worry about "de-vigging". Sports books odds can also be viewed as "% of wager returned"...ie +200 odds is just 100% of your wager returned on a win. +300 odds is just 200% of wager returned....plug this into Kelly criterion formula for your bet size and your good to go....
>
> **u/DotSlashSports** (1 pts): No problem. I'd listen to some of the Spotify podcasts with the person who did DARKO. His name is Kosta. I'm sure you will get some good nuggets of info from them.
>

---

### [Soccer Value Betting Team](https://reddit.com/r/algobetting/comments/120mki5/soccer_value_betting_team/)
**Author**: u/AssignmentHelpful | **Score**: 8 | **Comments**: 8 | **Date**: 2023-03-24

Hey pals, I’m looking to build a small team (3-5 people) to develop a system to price the following soccer markets: moneyline, over/unders and Asian handicaps. 

I recognize the difficulty in pricing soccer given the popularity of the sport, the high cost of data and the competition from big betting syndicates, but I believe there are pricing inefficiencies that we can exploit using feature engineering on event data. The development of the infrastructure will most likely take between 5-10 months with the right people. I have already tackled some of the scrapping and data wrangling required, but I’m still far from having a streamlined system.

The project will entail:
- Scrapping and cleaning event data (started)
- Scrapping and cleaning odds data (started)
- xG, xThreat model implementations (started)
- Feature engineering 
- Developing machine learning modes
- Testing accuracy of the models
- Deploying everything to servers/cloud

This should be a fairly big project, so I don’t expect many of you to be interested. 
The worst case scenario is that we don’t find any edge, if that’s the case we would still have the infrastructure to do any other projects regarding soccer. 

Let me know if you are interested or if you are just curious about the project and it intricacies.

PD: I’m coding in python and storing data in SQL

**Top Comments:**

> **u/TheBigLT77** (1 pts): New to algo but ten years betting on soccer and played at a high level. Happy to help
>
> **u/yungreseller** (1 pts): I’d recommend a different sport, if you print the premium free pinnacle odds against the odds implied by results, you usually find that if there are mispricings they are usually covered by the bookies premium. I mean think about it, in this market alpha can only exist for you, if you are the only one knowing it.
>
> **u/AssignmentHelpful** (1 pts): The idea would be to develop models that beat the closing line on sharp bookmakers (pinnacle and betcris), so that you can consistently bet sizeable amounts on these sites without the danger of getting restricted or banned. Way easier said than done, but I’m certain that it’s achievable on some markets.
>
> **u/boardsteak** (1 pts): How do you expect to capitalize on your results?
>

---

### [Best Algorithmic Market Making Strategy?](https://reddit.com/r/algobetting/comments/1ieed8t/best_algorithmic_market_making_strategy/)
**Author**: u/nvng | **Score**: 7 | **Comments**: 9 | **Date**: 2025-01-31

Most of the content I see on this sub is about building a profitable model to predict the outcome of a match, but whats the best way to make money once we have a good model? Seems that most people are just doing straight EV bets but MM strategies on exchanges sound way more attractive. No limiting/banning, often can bet higher volumes, and some of these exchanges even offer rebates for high volume. 

So what goes into these algorithmic market making strategies? Is it just simple mispricing, i.e. you find a theoretical value and quote the market at a profitable margin? Or is it more complex where people are building advanced hedges and grouping bets to create spreads.

**Top Comments:**

> **u/BetBrotherApp** (1 pts): As a rule of thumb bookmakers always have the most accurate models plus an edge. 

Try to compare prices across a range of bookmakers and look for differences. The research paper “Beating the bookies with their own numbers - and how the online sports betting market is rigged” is a decent paper on this. 

Line movements is incredibly important, as well as placing bets early enough before the odds drop

Lastly looking at psychological factors plays a role, often times markets are mispriced due to overall sentiment not actual data
>
> **u/neverfucks** (1 pts): if you put up a sign that says "i'm willing to sell eagles +1.5 at -105 and buy eagles +1.5 at +105" you are not only a market maker, you're a sportsbook operator and you need a license unless you are doing your market making on an exchange like novig that is legal in your state.
>
> **u/redtwinned** (1 pts): Huh, didnt know you could do that. I live in a state where books aren’t legal but fantasy apps are, so I’m on a friend’s book. Normally he has me generate lines for local games that aren’t offered by his website that he uses. Maybe I should talk to the backers about getting a deal lmao
>
> **u/BowTiedBettor** (1 pts): and some of these exchanges charge hefty fees on profits
>
> **u/neverfucks** (1 pts): market making. you put up a sign that says "i'm willing to buy up to 50 apples from anyone for a dollar and i'm willing to sell up to 50 apples for a dollar 5" and bam you are making a market in apples. if you sell as many apples as you buy, you've done well as a middleman and you make a profit. if people are much more interested in either buying from you or selling to you, you need to move your prices or you will get trucked. welcome to capitalism baby
>
> **u/grammerknewzi** (1 pts): What difference is there between market making and showing two sided lines like a book does? Both are accepting two sided risk for enough edge.
>
> **u/jbet13** (1 pts): It’s called market making, also not necessarily looking for equal volume
>
> **u/ZeltronTheHellspawn** (1 pts): https://preview.redd.it/vrq40qkpcfge1.jpeg?width=250&amp;format=pjpg&amp;auto=webp&amp;s=79a55c13c2e4b775f43bfc3a21ce82dd1a10a20e
>
> **u/grammerknewzi** (1 pts): pretty sure this is just called being a book; your really just scalping odds by hoping you get large, but equal volume on both sides of a spread for example.
>
> **u/jbet13** (1 pts): Don’t think anyone will give away the secrets of this one but just remember 
- adverse selection 
- nice prior price 
- move with money 
- know where high variance price moves may occur
>

---

### [Types of stat/cs college classes for better intuition and knowledge for sports modeling?](https://reddit.com/r/algobetting/comments/1fnnvho/types_of_statcs_college_classes_for_better/)
**Author**: u/GeometricBison9 | **Score**: 5 | **Comments**: 7 | **Date**: 2024-09-23

Hello, I am a college student studying essentially a dual degree in CS and Stats. I’ve been betting for 7 months through a discord and have an 18% ROI on pikkit. I am very interested in trying to beat the books using my own data analysis and modeling. For those who have this background, what types of classes are important for this type of work? I know a huge part of finding edges is analyzing Sportsbooks odds and EV, but I was wondering what type of statistical stuff is good to take?
I have pretty solid CS knowledge and can learn stuff pretty quickly, and I already have done quite a bit of web scraping, web dev, and basic ML with scikit and PyTorch.

My repertoire: stat modeling, lin alg, calc3, stats and prob, stochastic processes, data structures, artificial intelligence

Any advice is greatly appreciated!

**Top Comments:**

> **u/__sharpsresearch__** (11 pts): The biggest hurdle i see everyone here with is the fact that ~~no one can~~ most people cannot program properly. You will be able to move faster and learn more than anyone if you can understand how to create a psql database and stand up a server on digital ocean.

programming is 95% of the work to be good at algobetting. Most "AI" in algobetting is best done with xgboost, logistic or linear regression so know these really well, calc/advanced datastructures are borderline useless.

Learn as much about feature engineering as you can.
>
> **u/jbr2811** (4 pts): To piggy back off of this, scraping lines and stats and managing a database of all that info is a huge part of it. Focus on programming first of your intention is to originate your own numbers.
>
> **u/Shallllow** (2 pts): It's not a be-all end-all, just more flexible. I'd wager the best DL people are better than the best LGBM/XGBoost people, but the median case is better for boosting. Not sure what your point is with the latter, some other kind of model?
>
> **u/fysmoe1121** (2 pts): and not getting IP banned for web scraping off sites you’re not suppose to lol
>
> **u/Mr_2Sharp** (1 pts): Strangely enough feature engineering wasn't taught in any of my classes but it's basically the most important part imo. You can have chatgpt get you 80% through to running a model in Python the rest will take you anywhere from 20 minutes to an hour depending on your experience. Feature engineering on the other hand is an entirely different beast and can take enormous amounts of time from gathering, organizing, and cleaning data to having the mathematical maturity and insight to create your own features. This is expedited by having programming skills as others here have said. So definitely learn to feature engineer in some programming language. As to which language is optimal is anybody's guess.
>
> **u/KolvictusBOT** (1 pts): Doubtful deep learning is the be-all end-all answer. I did not mention deep learning on purpose. But you can go beyond dumping csvs into xgboost. And in the future, I highly doubt that that(xgboost) will in any way provide you an edge over the market as a small-time operation without data that others lack.
>
> **u/Shallllow** (1 pts): Models can only be as complex as the amount of data you have, high frequency trading? Sure, deep learning is gonna be on top. Betting on 10s or 100s of games? Having a solid understanding of fundamental stats, good prior assumptions, and quality data is much more important.
>

---

### [Beating books on NBA Props](https://reddit.com/r/algobetting/comments/1kf2o9j/beating_books_on_nba_props/)
**Author**: u/Consistent_Buy625 | **Score**: 3 | **Comments**: 1 | **Date**: 2025-05-05

I’ve been testing a few different models against NBA player props (points, assist, rebounds) to see how they compare to sportsbooks. I’ve been using things like the way back machine on rotowire to obtain large amounts of previous props at once. I’m wondering if it’s worth also testing across playoff seasons to see if there is any variance due to playoff performance from players being different than the regular season, and also how much of an edge I would need in order to break even/become profitable

---

### [How sharp really is FanDuel on NBA props?](https://reddit.com/r/algobetting/comments/1keycjh/how_sharp_really_is_fanduel_on_nba_props/)
**Author**: u/jcmmania | **Score**: 3 | **Comments**: 4 | **Date**: 2025-05-05

I have heard through the grapevine multiple times that FanDuel is sharp on NBA player props. For this reason, as a top-down bettor I’ve been avoiding betting NBA player props into Fanduel, even when they diverge significantly from the rest of the market including actually sharp books like Pinnacle. Am I overrating Fanduel in this regard? Also, how does time from tip-off play into this (i.e. does Pinnacle’s edge over Fanduel increase as they take more sharp action on a given game)?

---

### [Underdog NFL +EV Record by Week](https://reddit.com/r/algobetting/comments/1iolda6/underdog_nfl_ev_record_by_week/)
**Author**: u/FavoredProps | **Score**: 2 | **Comments**: 0 | **Date**: 2025-02-13

**What’s up! We graphed the hit rate for props identified as +EV on the Underdog DFS site for the 2024 NFL Regular Season.** 



**Approach:**

⁃    Included standard-payout props with -125 or better average odds from 4+ sportsbooks

⁃    Props with line changes were considered separate props

⁃    Since we had 15 minute snapshots of data, the last occurrence of a prop was used to prevent duplicates



The **overall hit rate for the regular season was 54.6%** over 3601 props that were included in the approach above. For context, the **breakeven hit rate for each pick in a 6-leg flex parlay is 53.8%.** 



**Also, “Under” +EV props are more accurate and made up just 40% of the total count.**

⁃    Over: 53.9%

⁃    Under: 55.7%



It seems like blindly tailing +EV plays this season would’ve earned a small profit. To help get those numbers up, we made a Free Player Prop Tool [https://www.favoredprops.com/dfs/nba](https://www.favoredprops.com/dfs/nba) to research more data points like defensive rankings, line movement, and hit-rate in various situations



**Let us know if you’d like to see more content like this!**

https://preview.redd.it/553omucibxie1.jpg?width=1440&amp;format=pjpg&amp;auto=webp&amp;s=858e96555ef6bd79da1384c5d62ee3dc61b38483

---

### [Live expected value betting?](https://reddit.com/r/algobetting/comments/111jg9a/live_expected_value_betting/)
**Author**: u/Quirky-Discount6828 | **Score**: 2 | **Comments**: 6 | **Date**: 2023-02-13

Assuming that you can you get to the line and place your bet before the odds change, are there any other pitfalls for live expected value betting? In fact, wouldn’t this increase your chances considering it would allow books to change odds from their closing line to a more accurate interpretation of how the game is actually being played out?

---

### [Fractional Kelly Criterion approaches?](https://reddit.com/r/algobetting/comments/m7lknn/fractional_kelly_criterion_approaches/)
**Author**: u/simiansays | **Score**: 1 | **Comments**: 18 | **Date**: 2021-03-18

Hi, do folks here use the Kelly Criterion? Just wondering what approaches you use for translating a Kelly number into an actual allocation.

At the moment, I'm just doing a 15% fractional Kelly but wondering if anyone has spent much time tuning Kelly-based allocations. I vacillate between thinking 15% is too agressive or too conservative. Most of my positions end up being around 1-5% of bankroll. I picked this number to minimize drawdown risk but am toying with the idea of increasing it slowly as the bankroll grows and I get a better feel for the model.

I'm also moderating my model's perceived edge to reduce the instances of huge Kelly recommendations - at the moment, I'm just chopping all perceived edge in half which feels about right.

The main drawback I see right now is that it feels like I'm under-allocating the rarer longshots where the perceived edge is large, and based on my results the real edge was also large but the Kelly recommendation for those plays using this system was very small (usually \~1% of bankroll). Curious if anyone has encountered the same thing.

This article was the most mathy one that I could still (mostly) absorb on the topic: [https://caia.org/sites/default/files/AIAR\_Q3\_2016\_05\_KellyCapital.pdf](https://caia.org/sites/default/files/AIAR_Q3_2016_05_KellyCapital.pdf)

---

## Feature Engineering

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [MMA AI &amp; Project Sharing](https://reddit.com/r/algobetting/comments/jzhyqk/mma_ai_project_sharing/)
**Author**: u/akkatips | **Score**: 9 | **Comments**: 3 | **Date**: 2020-11-23

Recently, we've created an MMA AI which predicts the outcome of UFC fights. There are numerous variables used ranging from each fighter's reach to the number of KO wins they've had in the UFC to the number of strikes they threw last fight. All these variables are inputted into the AI each week and as a result generates predictions. 

The backtesting of the AI gave us some very promising results (Since Jan 2019):

**Total Profit: +49.63U** 

**Average Profit per Event: +0.64U**  

**Average ROI: +8.67%** 

**Here are the graphs showing this in a more visual format:** [**https://imgur.com/a/Fdu0oSq**](https://imgur.com/a/Fdu0oSq)

We have also been working on an extra MMA AI that aims to predict whether a fight will go the distance or not. Last weekend we were able to combine the predictions from both AIs to predict a 6.50 odds winner at the weekend, we even pre-posted it on Reddit!

Has anyone else been working on some interesting projects and found profitable strategies as a result?

**Top Comments:**

> **u/bluelotus214** (1 pts): Wicked.  I'm looking for some data on this.
>
> **u/RepresentativeDig921** (1 pts): Strategy.

Bet every single MMA dog like this

Win

By TKO, KO

By Submission

Profit.
>
> **u/plinifan999** (1 pts): Hello! Several questions:

\--How do you get your data?

\--What type of model are you using?
>

---

### [Soccer Value Betting Team](https://reddit.com/r/algobetting/comments/120mki5/soccer_value_betting_team/)
**Author**: u/AssignmentHelpful | **Score**: 8 | **Comments**: 8 | **Date**: 2023-03-24

Hey pals, I’m looking to build a small team (3-5 people) to develop a system to price the following soccer markets: moneyline, over/unders and Asian handicaps. 

I recognize the difficulty in pricing soccer given the popularity of the sport, the high cost of data and the competition from big betting syndicates, but I believe there are pricing inefficiencies that we can exploit using feature engineering on event data. The development of the infrastructure will most likely take between 5-10 months with the right people. I have already tackled some of the scrapping and data wrangling required, but I’m still far from having a streamlined system.

The project will entail:
- Scrapping and cleaning event data (started)
- Scrapping and cleaning odds data (started)
- xG, xThreat model implementations (started)
- Feature engineering 
- Developing machine learning modes
- Testing accuracy of the models
- Deploying everything to servers/cloud

This should be a fairly big project, so I don’t expect many of you to be interested. 
The worst case scenario is that we don’t find any edge, if that’s the case we would still have the infrastructure to do any other projects regarding soccer. 

Let me know if you are interested or if you are just curious about the project and it intricacies.

PD: I’m coding in python and storing data in SQL

**Top Comments:**

> **u/TheBigLT77** (1 pts): New to algo but ten years betting on soccer and played at a high level. Happy to help
>
> **u/yungreseller** (1 pts): I’d recommend a different sport, if you print the premium free pinnacle odds against the odds implied by results, you usually find that if there are mispricings they are usually covered by the bookies premium. I mean think about it, in this market alpha can only exist for you, if you are the only one knowing it.
>
> **u/AssignmentHelpful** (1 pts): The idea would be to develop models that beat the closing line on sharp bookmakers (pinnacle and betcris), so that you can consistently bet sizeable amounts on these sites without the danger of getting restricted or banned. Way easier said than done, but I’m certain that it’s achievable on some markets.
>
> **u/boardsteak** (1 pts): How do you expect to capitalize on your results?
>

---

### [Moving past the Basics (EPL)](https://reddit.com/r/algobetting/comments/psbvxy/moving_past_the_basics_epl/)
**Author**: u/ProdigyManlet | **Score**: 6 | **Comments**: 12 | **Date**: 2021-09-21

Hi everyone, I'm looking at creating an algorithm that predicts the outcome of EPL matches and provides the odds for value-seeking (seems the easiest place to start given the popularity and availability of data). The introductory approach seems to be modelling the expected goals scored by both teams using a Poisson distribution, which is a nice and intuitive model to start with (at least for someone with a bit of an applied stats background).

I'm now looking into more advanced classification methods that predict the outcome of a match between two teams. So far my classification model is getting 50% accuracy using only historical match result data (slightly transformed), so hopefully that's a good starting point. I've got some ideas for more features to add from reading a few papers and some intuition (e.g. manager data, weather, etc.), but was wondering what others found was effective or if they had any lessons learned in moving forward on the modelling side?

This might be too open ended, but some common themes and areas of interest I thought my be relevant to others are:

* How were people's experience with tmproving the basic models (e.g. Poisson) versus moving to classification models (e.g. traditional machine learning)?
* Aside from train/val/test data splits &amp; backtesting, what other techniques did people find effective for evaluating the accuracy or the reliability of their algorithm?
* Did anyone find any common misconceptions? (E.g. chasing down weather data only to find it's impact on model performance was limited).
* Any general types of data aside from match results/historical goal performance that were found useful?

**Top Comments:**

> **u/Davidweb1337** (3 pts): Im not experienced with running models or machine learning so i don't know what kind of data you're looking for. But from what I've heard in the industry, it's been very difficult to find live data feeds for League of legends, especially in China since the organisation running the tournaments over there are apparently not selling any live feeds to betting companies, often leading to latency issues and poor trading on the bookmaker's side. It's usually an esports trader manually adjusting odds while watching the stream haha. Or no live betting offered.

From what I could find, someone has already attempted to build a model here: (includes a link to a dataset, under downloads &amp; tools) https://www.quantumsportssolutions.com/blogs/league-of-legends/a-predictive-model-of-league-of-legends-game-outcomes
>
> **u/lequanghai** (2 pts): Where do you get data for esports? I mostly play and follow League of legends but cant find any complete dataset or source to perform analysis &amp; live betting.
>
> **u/Davidweb1337** (2 pts): E-sports is quite inefficient actually. It has only really started ramping up in the past few years but is still dwarfed by most traditional sports so bookmakers don't really invest as much into R&amp;D for it. You're very likely to find stale prices/lines here, but also very low betting limits.
>
> **u/bananarepubliccat** (2 pts): Yes,  most of the things you mention perform pretty poorly in reality.

Rolling window methods aren't that useful. You want to use season data with possibly priors from the previous season. Again, it is how information gets incorporated. With filter models, the update cycle is capturing all the right information...with rolling windows, you are getting some approximation of skill using unimportant information (against weak opponents, very old matches, etc.). You can weight more recent matches but it still won't beat ELO.

Btw, I didn't make this totally clear in my previous comment: the reason why these sports are hard to model is because the data is adversarial. The information comes from interactions between two teams, it is not only team skill but opponent skill that matters. This is particularly bad in football because you can have teams that win by doing things that would cause other teams to lose (this is less common in other invasion sports where there is usually a dominant strategy)...for example, if you have a model based on possession, teams that counter-attack will be rated poorly...and even then, that counter-attack strategy may only work against certain kinds of teams. And then you have a difference between offensive and defensive strategies: for example, Newcastle always used to outperform vs good teams because they were so defensively solid, but lost it whenever they had to attack the other team. It is very tricky. So an ELO model that has far less data will outperform because the ratings and difference of ratings capture the maximum amount of information.

If you are able to use some non-parametric grouping and then incorporate that into your rating then I think you would be able to produce a more traditional ML model that works (i.e. this team is a counterattack team against an attacking team so we expect X fast breaks, and they got X+5 so we increase their rating)...but even then, I still think the update cycle of filter models like ELO is very effe [...]
>
> **u/king-chungus** (2 pts): Don’t do deep learning, but I definitely think log regression, SVMs, etc… can be viable
>
> **u/ProdigyManlet** (2 pts): Thanks for the extremely detailed reply, this is absolutely awesome and is riddled with great info that answers a whole bunch of my questions (and some I hadn't even thought of yet).

By classification and traditional machine learning I'm referring to things like logistic regression, decision trees/random forest, support vector machines, etc. Basically traditional machine learning is non-deep learning methods. I definitely think Deep Learning would perform pretty poorly in most betting algos given the small data quantities.

In terms of data, I was using a rolling window (e.g. N games like you mentioned) that rolled across prior seasons to avoid the issue of say if N = 20, but we're at match 5 then there's only 4 data points. Obviously a lot changes between seasons which is not accounted for, but I was hoping to factor in information that captured these changes later on (i.e. manager changes/metrics and some form of player metrics). The Brier score looks good, and I like the idea of the ELO approach as it's much more manageable, simple and looks like it will be less reliant on across-season data; will look into all of these.

I had a feeling that the bigger markets will be more difficult. I will still try to get my basic model framework up and running using EPL, and then switch to some local leagues in my own country (looks like I can get the same data in basically the same format so should be an easy switch). I wanted to stick with a sport I have good domain knowledge in as I want to keep it interesting as a hobby while reviewing my classical statistics knowledge (I'm experienced in Deep Learning and Traditional ML, but it's been a while since I went back to the basics of distributions). However, I'll definitely take the suggestion onboard and look at some more obscure markets on the side. I was thinking of E-Sports but I would assume that might be quite efficient too.
>
> **u/TraptInaCommentFctry** (1 pts): &gt;you only update when you see something unexpected, the whole measure is weighted against peers

could you clarify what you mean by this?
>
> **u/bananarepubliccat** (1 pts): That isn't what I said.

I have used data that costs $100k+ annually, the features don't matter if you start from the wrong place (I explained this above, if you are seeing similar predictive power from ELO as ML then you have gone very wrong because ML, as most people are doing it, doesn't work...tbf, most people don't do ELO right either but that isn't a problem with the model). This varies by sport but the OP asked about soccer.

Using ELO as a feature is a basic error (and again, you are missing the point massively). ELO is just a filter, so you can use your ML model as an input to ELO: it is just a map from joint distribution of skill to prediction for a feature, so you can use ML as an input to ELO (I wouldn't advise building a mixture with ELO either, that is a very bad idea practically for soccer because of lineup changes).

How you do this is more complex but the key is that you are modelling a joint probability, that is where the power comes from. What OP will have tried is: X feature over N games or something similar, these models don't work (you can modify features, but it still won't get close). You can get them into a joint probability but, again, the problem is that they don't represent information correctly (again, this is obvious when you think carefully about what you are actually modelling...most people, inadvertently, end up with a single distribution for the average team...this works particularly poorly in soccer where there is no strategic equilibrium i.e. the meaning of features varies hugely based on the team).
>
> **u/MathMod3ler** (1 pts): Thanks for clarifying the original comment. Respectfully, I disagree that traditional ML is incapable of handling that amount of information. I think it comes down to having good features. Although, in practice I prefer using several ELO models as features in my ML models. So I definitely like the information ELO captures.
>
> **u/MathMod3ler** (1 pts): I disagree with a lot of this thread. Although, I think reasonable minds can disagree on this sort of stuff. I would say a couple things to take your modelling to the next level:

1)Stack uncorrelated models.
2) Use the betting market as a starting point for some of your models. The betting market is already a damn good model. Build on top of it, it already takes into account many of the basic features (probably including Poisson Distribution of goals). 
3) Come up with different targets. Ex: Win-Loss Binary and Difference in goals (they both tell you the betting outcome but the computer will look at them very differently).
4) Have way bigger test-validation sets than the normal rules of thumb. Finding patterns is easy...finding persistent patterns is hard.

My two cents, classification is fine. Just really do a lot of safe-guards and validation.
>

---

### [NFL Passing Attempts Model Advice](https://reddit.com/r/algobetting/comments/1k67adj/nfl_passing_attempts_model_advice/)
**Author**: u/toddinvesterguy12 | **Score**: 5 | **Comments**: 7 | **Date**: 2025-04-23

Hey everyone, I just tried for the first time to build a model that predicts a players pass attempts. I collected 3 years of data via scraping/APIs with columns formatted as 

Date of game,
Player,
Pass attempts in game,
Players team at time of game,
Home/Away,
Opponent team,
Player’s Coach,
Game start time,
Location of game,
Average temperature during 4 hours from start of game time,
Type of precipitation if any,
How many hours in four hour window precipitation occurred,
Pre game points total at fanduel and DraftKings,
Pre game total odds at fanduel and DraftKings,
Pre game spread for players team at fanduel and DraftKings,
Pre game spread odds for players team at fanduel and DraftKings,
Pregame pass attempts total at fanduel and DraftKings,
Pregame pass attempts odds at fanduel and DraftKings

I have minimal experience with coding (2 intro level courses in python and R), so I loaded this data into Claude and promoted it to create linear regression and random forest models with the data. I prompted it to train on half and test on the other half. Both achieved an r2 of around 0.4 so not good. 

At this point, I’m curious if I’m trying to predict a metric that is too volatile, if I need more data using the same features, if I need to add additional features, a combo, or if I’m missing something else I should learn about before proceeding. 

Appreciate any advice.

**Top Comments:**

> **u/cortezzzthekiller** (6 pts): Props are generally about predicting volume -- and passing attempts is ALL about volume. So you are missing a huge part of the puzzle here -- off/def plays per game
>
> **u/2kungfu4u** (2 pts): Huge agree here. I'd also argue in tandem with that you'd mostly likely want to include metrics like pass rate over expectation, pass rush splits on a given team and maybe even team record. It's one thing to include the spread indicating if they're a dog or not but how often they are a dog is valuable as well imo
>
> **u/Golladayholliday** (2 pts): I mean… What is the point of this model? To beat the books? To do some learning? 

You included the book odds, any good model is just going to violently latch on to that with the other things you have included(missing some major pieces). You very likely have built a devigger 😂. This is where the journey starts tho. Keep on pushing. 

I think the best piece of advice I can give you is what I wish someone had told me. ML/AI isn’t magic, it’s an extension of your expertise. You can huck a bunch of data at a model and you might get a okay baseline, but that is not what makes a model great. You need the domain knowledge and ML knowledge to know what is important and how to present (feature engineer) it, and if done right it will come to very similar conclusions as an expert would. 

The difference is it can do it in less than a second instead of an in depth time consuming expert review. That’s the magic.
>
> **u/Golladayholliday** (1 pts): It’s going to be tough only because you’re essentially feeding a much better model back into your model as an input that’s likely considering all the same things you are plus a lot more. 

The other thing to accept is most bets there is no +EV side. I have a very solid baseball model, and if I had to estimate about 80% of the time I get some number that’s between the spread(both sides lose money long term), 10% it’s very light value (picking up a quarter or 2 of EV on my $50 bet) and 10% it’s decent.
>
> **u/toddinvesterguy12** (1 pts): Essentially I want to connect the predictions it makes to +EV sides on passing attempt bets. For now I just need to learn more about machine learning and how best to present data to these models and I really appreciate your insights
>
> **u/toddinvesterguy12** (1 pts): Appreciate it that’s a great idea
>

---

### [How useful is something like this](https://reddit.com/r/algobetting/comments/1k662a4/how_useful_is_something_like_this/)
**Author**: u/Forsaken-Hearing3540 | **Score**: 4 | **Comments**: 17 | **Date**: 2025-04-23

www.playerprobabilities.com

I’ve been working on a machine learning model to predict NBA player props — specifically points, assists, and rebounds. Originally, I used linear regression (with Lasso for feature selection) and rolling averages to predict raw values. That alone gave me around 57  - 70% accuracy on some given days, this is for 68+ players on game days.

Now I’ve taken it a step further:
I treat the regression prediction as a mean,
Calculate a confidence interval using a z-score (95% confidence),
Run Monte Carlo simulations to estimate the distribution of outcomes,
Then compute the probability a player hits the over/under line.

Also a second reason why I am here ,can you guys share any tips on how you guys account for lineup changes and how it affects what a player is going to score. I have really been struggling with that aspect of things.l

---

### [Feature Engineering CFB Win-prediction Model](https://reddit.com/r/algobetting/comments/1g4djdx/feature_engineering_cfb_winprediction_model/)
**Author**: u/Durloctus | **Score**: 4 | **Comments**: 0 | **Date**: 2024-10-15

Anyone wanna talk predictors for CFB models?

I have a model I’ve had some success with last season and this season (so far) and I feel good about the features I’m using (ypg, off and def success rates, first downs per game, and an engineered feature that gives a ‘grade’ for game per the score margin and strength of opponent) but wondering what some of you feel are the best predictors for winners of games.

My goal a is give a &gt;= 5% return on money bet (moneyline only) for the cfb season, weeks 6-13. Last season saw a 14.83% return and this season is at 8% through two weeks.

---

### [Dive into Advanced Feature Engineering for Hong Kong Horse Racing Predictions!](https://reddit.com/r/algobetting/comments/1fksy1y/dive_into_advanced_feature_engineering_for_hong/)
**Author**: u/SohilRaceQuant | **Score**: 4 | **Comments**: 1 | **Date**: 2024-09-19

🏇 **Explore Hong Kong Horse Racing Predictions!** Are you as passionate about data and horse racing as I am? Let's delve into the numbers together and see what stories they tell.

🌟 **Opportunity for Collaboration:**

* **Data Sharing:** I’m eager to share my Hong Kong racing data with those interested and explore your datasets as well.
* **IP Acquisition:** I'm also considering purchasing innovative methodologies or unique datasets to boost our predictive models.
* **Partnership Potential:** Let’s discuss how we can collaborate in ways that enrich both our projects.

🤔 **Feature Engineering Discussion:** What factors do you consider essential? I'm excited to discuss different feature engineering techniques and learn from your experiences. Whether it’s discussing established methods or exploring novel approaches, let's push the boundaries of what we can achieve in horse racing analytics.

🔗 **Connect and Collaborate:** Reach out if you're interested in building something great together in the world of horse racing analytics!

---

### [Feature engineering for horse racing?](https://reddit.com/r/algobetting/comments/gs0vu1/feature_engineering_for_horse_racing/)
**Author**: u/[deleted] | **Score**: 3 | **Comments**: 3 | **Date**: 2020-05-28

---

### [MLB Predict Relief Pitchers](https://reddit.com/r/algobetting/comments/1eadw7c/mlb_predict_relief_pitchers/)
**Author**: u/pipicks | **Score**: 2 | **Comments**: 5 | **Date**: 2024-07-23

I've created an MLB model which is currently seeing success in betting first 5 innings totals/spreads (relatively low sample size, but have been getting good clv so far). I want to extend this model to full games. The model is heavily reliant on the individual players in a lineup, so, currently the rotowire projected starting lineups are being used. 

Now I have ideas on how to model when the pitcher swap will happen, but I'm looking for suggestions on predicting the relief pitcher(s) that come on. My current thoughts are to look at past starts for the starting pitcher and obtaining a categorical distribution of possible (active) relief pitchers. I'm not a huge baseball fan so I don't know how naive this is. I appreciate any input.

---

### [Best way to use past XG data as a model feature for pre-match betting?](https://reddit.com/r/algobetting/comments/x4xgs3/best_way_to_use_past_xg_data_as_a_model_feature/)
**Author**: u/Bhagafat | **Score**: 1 | **Comments**: 5 | **Date**: 2022-09-03

If I have data sets such as from Understat which include XG, I can create a model off the back of this to predict things like final score, o2.5 yes/no, etc. for each match and backtest this. 

However without some kind of feature engineering for XG so that we have these features available to us before each game (e.g. avg XG past 6 games, etc.) this model would be useless for pre-match betting, because of course I don't know what the XG stats of a match will be until it happens.

I see a lot of people blindly resort to using Poisson probabilities, taking lambda to be the XG mean over x amount of games (inc. maybe some home/away weighting), but as accurate as Poisson can be it of course has its downfalls. I'd be interested to see if anyone has done some investigation into how to produce the best "pre-match statistics" involving XG. Has anybody got any links/reports/videos/etc. with some kind of discussion on best practices for feature engineering here?

Cheers

---

### [Odds Screen Recommendations?](https://reddit.com/r/algobetting/comments/113kr7r/odds_screen_recommendations/)
**Author**: u/zahaha | **Score**: 1 | **Comments**: 7 | **Date**: 2023-02-16

Anyone have a good odds screen that is either free or reasonably priced? The more features the better but it doesn't have to be overly complex. At the minimum I need up to date lines from the legal books and it has to include Tennis. 

Right now I am getting robbed by Oddsjam and will be cancelling my subscription this month. I like Betstamp. It is great for a free tool but does not have as many features as OddsJam. Ideally, I want something that I can easily pull into excel. A free API would be ideal. Bonus points for a site that shows low hold and arb opportunities. Would like to have live lines but don't need them.

---

## NFL / Football

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [A tool for analysing odds](https://reddit.com/r/algobetting/comments/yd86kl/a_tool_for_analysing_odds/)
**Author**: u/_rbp_ | **Score**: 13 | **Comments**: 8 | **Date**: 2022-10-25

I have created an application for analysing odds – [www.rationalbets.com](https://www.rationalbets.com). It allows to identify profitable sports bets using the concept of expected value. I would be very grateful if you could check it's handy and provide feedback.

All you have to do to use it is:

· Choose an event from the sidebar or add a custom one.

· Set the probabilities of the event outcomes to your best knowledge using intuitive sliders.

Based on the probability distribution you specify, the tool will calculate the expected profits of your picks.

The tool is regularly updated with odds for football, NFL, baseball, and basketball. There is also an article section on maths in gambling.

www.rationalbets.com

**Top Comments:**

> **u/consolationgoal** (5 pts): It looks like you are using straight probabilities from the bookmaker's odds, meaning that the equation is 1/odds = probability. Right?

That means your probabilities include the bookmaker's margin, which in turn shows the expected net to win as zero. In reality, given bookmaker margins, the expected net to win should start out as negative. After all, that's how they make their money. Only by adjusting the probabilities should you be able to move the expected profit to zero or positive. 

In the Leicester City - Man City example, Pinnacle odds are 10.09 x 6.20 x 1.30. That means the bookmaker margin is 2.9% 

(1/10.09) + (1/6.20) + (1/1.30) = 1.029

So unless a person moves the sliders, it the net expected profit from a 10 euro bet should be -0.29 right?
>
> **u/_rbp_** (3 pts): I think there are a few good arguments against parlays:

1. As good as you might be at predicting events, you can't always get everything right. Losing parlays happens often, as the probability of winning decreases exponentially. For example let's say you place 5 bets, each one with a 90% chance winning (as sure as you can be of an outcome in most cases). The chance of winning a parlay is only 90%\^5 = 59%.
2. Parlays are bets with large odds, but a small probability of a payout. Such types of bets drastically increase the variance of your winnings. In other words, you have a larger chance of winning big, but also a larger chance of loosing big. I actually have a nice simulation of that in my [article on variance](https://www.rationalbets.com/articles/#variance).
3. There's one argument I don't think is necessary true, but probably is very often true - when placing a bet, you are paying the bookmaker his margin. The more bets you place in a parlay, the more this margin will increase (as it multiplies across all your picks).

These arguments aren't just theory - I don't believe any professional bettor would do parlays for the above reasons (unless from time to time for fun).
>
> **u/consolationgoal** (3 pts): Thanks for the explanation. You should check out the below paper, which gives great detail on how best to remove the bookmaker margin (including formulas). As you said, there is no exact certainty on how a given bookmaker does it, but the testing in the below paper makes clear the best option for the public to try to remove the bookmaker margin.

[https://www.football-data.co.uk/The\_Wisdom\_of\_the\_Crowd\_updated.pdf](https://www.football-data.co.uk/The_Wisdom_of_the_Crowd_updated.pdf)

I totally understand the desire to maybe not go crazy on precision, but professional sports bettors are often surviving on 1% edges (especially in the major sports like you've got on this tool), so I think precision is key.

More broadly, who is the target market for the tool? I feel like recreational bettors are unlikely to have a probability (even a reasonable range, frankly) for their desired bet, so they might not be able to take advantage of the tool. They are likely going to just line-shop, which your tool does help with but there are other more established options out there for that (Betstamp, etc). 

Originators - i.e. handicappers who create their own probabilities for an event - will be able to fairly easily determine their projected edge.

I don't really do parlays so I didn't check out that part of things, but it's true those probabilities are less well understood generally so that might be something that draws people's attention.

Looks like a lot of work went into the tool. Great job getting to this place.
>
> **u/Available_Remove452** (3 pts): I'm interested in trying this, thank you.
>
> **u/Loyalty4life187** (2 pts): How bout the guys on the book or the tube that wants to tell you how ya become a millionaire 🤣 and they ain’t even one..
>
> **u/_rbp_** (2 pts): I never really analysed picks, but my intuition is in most cases it might be the same as with "investment gurus" selling books - for most it goes, if they were really that good at predicting what will happen, they would simply be making money this way and not seeking a fee for sharing their wisdom.
>
> **u/Loyalty4life187** (2 pts): Sites because this year or maybe I’ve never noticed cause I never paid it no mind just used my own intuition is that what the experts tell people to pick I found that I’m not good at math but say for example SportsLine other night shot every pick wrong.  I mean right now it’s something to do ya know so I been doing basketball n football
>
> **u/Loyalty4life187** (2 pts): Yea I’m lost wish I knew what the heck was talking bout, I do parlays a lot n be off by like 1 game n what not.
>
> **u/_rbp_** (2 pts): Thank you! I hope for some feedback. The concept makes sense to me and works on my devices, and I hope to confirm it does for others too.
>
> **u/Loyalty4life187** (1 pts): I clicked on article what part/ NeverMind I got it
>

---

### [My attempt at a model to bet on NFL games](https://reddit.com/r/algobetting/comments/ggaz71/my_attempt_at_a_model_to_bet_on_nfl_games/)
**Author**: u/HamirTime | **Score**: 8 | **Comments**: 14 | **Date**: 2020-05-09

Hey guys, been lurking since this subreddit got created and knew I would be contributing to it once I got my model to an "acceptable" state to hopefully get further insight.

Gonna try to keep this as short as possible because alot of explaining happens in the Jupyter notebook, but here goes.

So basically I took a data mining course this last semester and the final project was to apply the concepts we learned in class to a real world scenario. While the NFL was in full swing, I was a frequent sports better and would really enjoy betting and watching the games. Data and modeling still seemed like such a complex topic to me, but I knew that eventually I would the subject either in class or on my own. After learning the data mining world, this in-class project was a perfect way to test what I had learned as well as try and use my skills to make some money.

SO with all that out of the way, the summation of the actual data and models is that I took game data from Kaggle (mainly used to pull the scores) and added full team rosters for both away and home teams (rosters scraped from another site). My thought was that since each team is composed of 52 players, that at the end of the day their performances (with the leadership of the head coach) is what determined the outcomes of the game. So to summarize, each of my records contained the home and away teams, current W-L records, and most relevant positions for both teams. I also decided to filter the data to only be within this millennia.

With this data I tried to use regression models to predict the score of the games. This score would then be compared with the vegas spread for that game so that the model could predict whether it should bet on the home team or the away team to cover the spread. This might not be a good practice, but I just decided to use every game from the 2000-2018 season to predict 2019 games as my model testing phase. I used the SVM Regressor algorithm (primarily because it was the only one that supported unbalanced data, which is obviously important since the more recent games should play a bigger factor) and an Artificial Neural Network because it's pretty easy to grasp and honestly doesn't require much thinking or work from me. Kinda also used it in case I was configuring the SVM wrong.

In summary, my results were slightly worse than I was expecting.  Both my models average out to about 52% accuracy and a mean squared error of around 195 when compared to the actual point values. Hence the main reason I am posting here: to get some help from more experienced data scientists.

I've decided to include my work here, both for more experienced people to critique and maybe for some less experienced people to learn. This project was, again, done as a school project so please excuse some of my markdown comments as they had to follow a format for the class. This is also done in Python primarily using scikit learn for all data modeling and pandas for pre-processing. I used VS Code as my IDE with the Microsoft Python plugin to view and edit Jupyter Notebooks.

I want to keep developing this in the future, at this point not even to make money but just because I think it's a cool concept. The thought of math being able to better predict as complex a game as football more accurately than almost anyone is crazy. Other than this model, I recently also purchased a Raspberry Pi (also being used for other side projects) to eventually automatically pull new game data for the model to predict.

Like I said above please feel free to critique, this was basically my first major python project and I had no experience with any of these libraries. Also don't usually post on Reddit so if my formatting sucks call me out on that too.

Thanks guys, hope this is a helpful post to keep the subreddit going.

Jupyter Notebook: http://www.filedropper.com/finalproject_2 (not sure how long the site will host the file TBH)

**Top Comments:**

> **u/15woodsjo** (4 pts): To piggy back off this answer, I would also throw in a suggestion of using a neural network and turning this into a binary classification problem.

In practicality this is a logistic regression model that you have more control over, and can potentially get a little bit better of a model out of the algorithm.

&amp;#x200B;

The reason I would suggest anything binary classification for this type of problem is you would want to be able to measure the % likelihood of one team vs. another covering the spread whilst the line moves. In essence, you can get more information by knowing that team A has a 60% likelihood of covering a (-9) line and team B has a 40% chance PLUS team A has a 55% likelihood of covering a (-10) line and team B has a 55% chance. Basically you want to be able to apply your model to a dynamic line to get what is hopefully a more accurate picture of a +EV game
>
> **u/KidMcC** (3 pts): Will respond more fully later, but one thing that jumps out at me is that you might want to explore using a GLM with Poisson distribution as opposed to something like SVMs for football scores. This allows you a better probability assignment to different outcomes. 

Basic googling should land you more stats-focused details on that.

As an aside, there are better ways to handle imbalanced data than using an SVM for assigning binary winner/loser status. SVMs rarely perform consistently better than some other such models, like Logistic Regression or Random Forest Classifiers. Looking into weighted logistic regression or sub-sampling to balance out data as opposed to picking a specific model family as a result.

&amp;#x200B;

Again, will respond more later, as it's an interesting problem. Also open to debate re: any of the above.
>
> **u/15woodsjo** (2 pts): That's fair, my background is in basketball where I suppose there is a larger sample size.
>
> **u/KidMcC** (2 pts): This is a very important distinction. "Binary classification" can be done at least two ways here.   
1) Linear model (of sorts) fit to predict the point difference (homeScore - awayScore). Again, GLM approach with Poisson Distribution is the most common choice for football for a reason, given how scoring is not linear with each point-accumulating event. The sign of the endogenous variable would then be indicating the "win" the same way a 1/0 would in your example. Here you can use size of the difference to indicate probability, to some degree.   
[https://www.sbo.net/strategy/football-prediction-model-poisson-distribution/](https://www.sbo.net/strategy/football-prediction-model-poisson-distribution/)

[https://www.pinnacle.com/en/betting-articles/Soccer/how-to-calculate-poisson-distribution/MD62MLXUMKMXZ6A8](https://www.pinnacle.com/en/betting-articles/Soccer/how-to-calculate-poisson-distribution/MD62MLXUMKMXZ6A8)

2) Ignore points and predict an actual binary variable indicating whether or not the home team won. What this modeling approach provides is a direct probability associated with each classification. This also requires a choice to be made of regularization, L1/L2 penalty if using Logistic Regression, etc.  


Predicting scores via regression, and then daisy-chaining that back into a spread comparison to then take advantage of error profiling, like you said, is quite indirect and will certainly introduce more bias and/or volatility than what it returns in accuracy.
>
> **u/KidMcC** (2 pts): If we are talking about predicting binary game outcome, then I'd be hesitant to go the route of neural network. By its very nature of scheduling and season construction, football doesn't offer a huge dataset of games to really draw from (compared to other sports). Especially if you aren't weighting games from the distant past fairly, one can find themselves with a high variance, over-parameterized model fit on too little an amount of data. All my opinion of course! 

I do think a thoughtful feature selection process fit to an XGB or RandomForest model might be more manageable given that gameplay data gets old fast. Exponential weighting can be your friend here, though, if you need to go way back, just make sure your offense-profiling is dynamic!
>
> **u/15woodsjo** (2 pts): You are implementing a binary decision based on your model but not using an algorithm that is trained using binary classification. Slight difference
>
> **u/HamirTime** (2 pts): Thanks for the insight, I will definitely look into GLMs and their applications. I'm more familiar with logistic regression, so I would probably err towards looking into that to better handle imbalanced data
>
> **u/HamirTime** (2 pts): I could be misunderstanding your suggestion, but I think I am currently already transforming this into a binary classification problem. After using regression to calculate the score, I compare it with the spread to calculate a 'class' variable (0 or 1). 0 meaning a bet should be placed on the away team and a 1 meaning a bet on the home team. I use these to also measure common metrics like accuracy, precision, and recall.

 The likelihood percentages was also something I wanted to implement by using the difference between the predicted score and the spread, but wanted to focus on improving the model before then
>
> **u/anxiousalpaca** (1 pts): You are right, i totally misread what is meant by daisy-chaining back (not an English native speaker)
>
> **u/KidMcC** (1 pts): The OP said nothing of features describing the relative defensive capability of either side of the ball. Without such features, I'd still say daisy-chaining yhat values for score back into a comparison is risky, as it leaves nothing in the model reflecting the fact that for one team's offense to have the opportunity to score, it generally requires that the other team does not have the same opportunity at the same time (save for pick-6s). Volatility would be unstable when you begin to use this approach with games where disparity between defensive capability on each side is substantial. At least, this is what I have found. Curious to hear more if this is still at odds with your experience.
>

---

### [NFL Play by Play Data](https://reddit.com/r/algobetting/comments/zlf6xu/nfl_play_by_play_data/)
**Author**: u/mxx24 | **Score**: 7 | **Comments**: 2 | **Date**: 2022-12-14

I've been looking for some more advanced play by play data for a new system, NFL fastr and its python equivalent have personnel and men in box frequencies, but I am looking for something containing the specific man, zone, and type of zone (2-high shell for example) for each play as well.   I've seen various users tout these percentages on Twitter, but cannot find a proper dataset to show for it. thanks.

Edit: I also build out various quant betting models for other sports, have been working on football as of late, happy to partner up if interested

**Top Comments:**

> **u/Louisville117** (1 pts): I tried for a while to see if AWS offered any of its data but sadly no. Would be great even if I had to pay for it. Tons of data in there.
>

---

### [NFL Passing Attempts Model Advice](https://reddit.com/r/algobetting/comments/1k67adj/nfl_passing_attempts_model_advice/)
**Author**: u/toddinvesterguy12 | **Score**: 5 | **Comments**: 7 | **Date**: 2025-04-23

Hey everyone, I just tried for the first time to build a model that predicts a players pass attempts. I collected 3 years of data via scraping/APIs with columns formatted as 

Date of game,
Player,
Pass attempts in game,
Players team at time of game,
Home/Away,
Opponent team,
Player’s Coach,
Game start time,
Location of game,
Average temperature during 4 hours from start of game time,
Type of precipitation if any,
How many hours in four hour window precipitation occurred,
Pre game points total at fanduel and DraftKings,
Pre game total odds at fanduel and DraftKings,
Pre game spread for players team at fanduel and DraftKings,
Pre game spread odds for players team at fanduel and DraftKings,
Pregame pass attempts total at fanduel and DraftKings,
Pregame pass attempts odds at fanduel and DraftKings

I have minimal experience with coding (2 intro level courses in python and R), so I loaded this data into Claude and promoted it to create linear regression and random forest models with the data. I prompted it to train on half and test on the other half. Both achieved an r2 of around 0.4 so not good. 

At this point, I’m curious if I’m trying to predict a metric that is too volatile, if I need more data using the same features, if I need to add additional features, a combo, or if I’m missing something else I should learn about before proceeding. 

Appreciate any advice.

**Top Comments:**

> **u/cortezzzthekiller** (6 pts): Props are generally about predicting volume -- and passing attempts is ALL about volume. So you are missing a huge part of the puzzle here -- off/def plays per game
>
> **u/2kungfu4u** (2 pts): Huge agree here. I'd also argue in tandem with that you'd mostly likely want to include metrics like pass rate over expectation, pass rush splits on a given team and maybe even team record. It's one thing to include the spread indicating if they're a dog or not but how often they are a dog is valuable as well imo
>
> **u/Golladayholliday** (2 pts): I mean… What is the point of this model? To beat the books? To do some learning? 

You included the book odds, any good model is just going to violently latch on to that with the other things you have included(missing some major pieces). You very likely have built a devigger 😂. This is where the journey starts tho. Keep on pushing. 

I think the best piece of advice I can give you is what I wish someone had told me. ML/AI isn’t magic, it’s an extension of your expertise. You can huck a bunch of data at a model and you might get a okay baseline, but that is not what makes a model great. You need the domain knowledge and ML knowledge to know what is important and how to present (feature engineer) it, and if done right it will come to very similar conclusions as an expert would. 

The difference is it can do it in less than a second instead of an in depth time consuming expert review. That’s the magic.
>
> **u/Golladayholliday** (1 pts): It’s going to be tough only because you’re essentially feeding a much better model back into your model as an input that’s likely considering all the same things you are plus a lot more. 

The other thing to accept is most bets there is no +EV side. I have a very solid baseball model, and if I had to estimate about 80% of the time I get some number that’s between the spread(both sides lose money long term), 10% it’s very light value (picking up a quarter or 2 of EV on my $50 bet) and 10% it’s decent.
>
> **u/toddinvesterguy12** (1 pts): Essentially I want to connect the predictions it makes to +EV sides on passing attempt bets. For now I just need to learn more about machine learning and how best to present data to these models and I really appreciate your insights
>
> **u/toddinvesterguy12** (1 pts): Appreciate it that’s a great idea
>

---

### [Need help with a simple regression model](https://reddit.com/r/algobetting/comments/qgivhc/need_help_with_a_simple_regression_model/)
**Author**: u/[deleted] | **Score**: 4 | **Comments**: 10 | **Date**: 2021-10-26

Hi, I am in a Business Analytics class and have a project requiring me to build a simple logistic regression model to predict in-game NFL win probability.

It was fairly simple and I pretty much got it down, except one small problem. The win probability for the winning team should be 100% by the end of the 4th quarter, however, my model is not able to calculate this. I feel like there is a simple solution but my brain is not quite grasping it (worst feeling LOL).

Can anybody assist? Thank you very much in advance :&gt;

---

### [NFL Football Model (starting in Week 3)](https://reddit.com/r/algobetting/comments/1fhsudd/nfl_football_model_starting_in_week_3/)
**Author**: u/[deleted] | **Score**: 3 | **Comments**: 4 | **Date**: 2024-09-16

---

### [Underdog NFL +EV Record by Week](https://reddit.com/r/algobetting/comments/1iolda6/underdog_nfl_ev_record_by_week/)
**Author**: u/FavoredProps | **Score**: 2 | **Comments**: 0 | **Date**: 2025-02-13

**What’s up! We graphed the hit rate for props identified as +EV on the Underdog DFS site for the 2024 NFL Regular Season.** 



**Approach:**

⁃    Included standard-payout props with -125 or better average odds from 4+ sportsbooks

⁃    Props with line changes were considered separate props

⁃    Since we had 15 minute snapshots of data, the last occurrence of a prop was used to prevent duplicates



The **overall hit rate for the regular season was 54.6%** over 3601 props that were included in the approach above. For context, the **breakeven hit rate for each pick in a 6-leg flex parlay is 53.8%.** 



**Also, “Under” +EV props are more accurate and made up just 40% of the total count.**

⁃    Over: 53.9%

⁃    Under: 55.7%



It seems like blindly tailing +EV plays this season would’ve earned a small profit. To help get those numbers up, we made a Free Player Prop Tool [https://www.favoredprops.com/dfs/nba](https://www.favoredprops.com/dfs/nba) to research more data points like defensive rankings, line movement, and hit-rate in various situations



**Let us know if you’d like to see more content like this!**

https://preview.redd.it/553omucibxie1.jpg?width=1440&amp;format=pjpg&amp;auto=webp&amp;s=858e96555ef6bd79da1384c5d62ee3dc61b38483

---

### [Technical analysis on sports](https://reddit.com/r/algobetting/comments/1k0euwc/technical_analysis_on_sports/)
**Author**: u/Zestyclose-Gur-655 | **Score**: 2 | **Comments**: 0 | **Date**: 2025-04-16

On the stock market technical analysis of charts is very popular. 

Usually bookmakers don't offer any charts at all. (But they don't even want people to win, they barely show you profit and loss because they rather hide people are losing.)  
Some betting exchanges have charts, betinasia also does. 

Does it make sense to use any charts for betting and why not? 

Maybe i'm crazy but i found if i analyse a game, sometimes it's quite obvious where the money is coming in on. Because bookies just keep moving the price on one side. You can basically see it on the chart where people have been betting on. It kind of tells the story of that particular market.

In theory if you have a chart where the odds are constantly dropping, you first back at a good price then later lay it. This creates some value. Or vice versa with odds that are becoming bigger, so less of a % chance. First lay it then back it. 

The problem is maybe events that are going one side don't have to keep going that side. I think it does slightly more often then not but this is just an assumption that i make, i don't have hard data on if steamers more often then not keep steaming. 

I'm just trying to think like a bookie right now, essentially they just back and lay bets with a spread in between. This is similar to market makers, actually it is a form of market making. The real value then to me seems to anticipate where odds are going to, more so then where they are now. This is also true for gamblers, and even gamblers are just trying to beat closing line value, get a better value themselves. This indicates a profitable strategy. So if odds move in your advantage more often then not, this is part of the goal to me it seems. 

Say you was a bookmaker, in essence the best thing for them is have some markets that just go sideways forever with a big spread. They can constantly buy and sell, buy and sell and make a profit. Often you do see that odds move a certain direction. For bookmakers this is somewhat of a loss because their odds where first not correct. This is also why you can only bet little when an event is days away and big when it nears to start. The price has to shape to where it should be. Once everyone made their bets they know pretty good where it should about be priced. 

Maybe i spend too much time on the stock market but i do see also just trends, mean reversions, support and resistance in betting markets. In fact i think betting markets are even way more logical then financial markets. There might also be manipulation by single actors but for a bookie it's not good if odds are much different then where the real odds should be. Mispriced events makes it possible to value bet, since only the outcomes in reality influences the outcome of a bet. On financial markets it's mostly just price alone that has any meaning, fundamentals to a lesser extent. Option contracts are based on the price of the underlying not on the outcome of events. So there is much more what George Soros would call: "reflexivity" possible. Even the market participants itself can influence reality.

---

### [Anyone know the status of MySportsFeeds.com?](https://reddit.com/r/algobetting/comments/105q4et/anyone_know_the_status_of_mysportsfeedscom/)
**Author**: u/postrema19 | **Score**: 2 | **Comments**: 4 | **Date**: 2023-01-07

Hi All.  Long time lurker/first time poster.  I have a background as software developer and am very interested in this space, but am finding it difficult locating a good source of historical data and/or feeds.

I  recently stumbled across what looked to be a promising API provider at [MySportsFeeds.com](https://MySportsFeeds.com), but have found them to be unresponsive.   The API and data modeling seem to be pretty mature and well organized, but I recently found that it is not returning data for NCAAM basketball, so I'm beginning to wonder if this site is now defunct.

Does anyone have any insight into the status of this provider?  If not, any recommendations in terms of other providers in this area would be well appreciated.  I am primarily interested in data for the "big four" of the US (NFL, MLB, NBA and NHL) as well as college basketball data.

Any help or direction is greatly appreciated!

---

## Soccer / Football

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [Tennis Analysis #2: Upset Victories](https://reddit.com/r/algobetting/comments/11v0289/tennis_analysis_2_upset_victories/)
**Author**: u/quant_boy123 | **Score**: 12 | **Comments**: 1 | **Date**: 2023-03-18

Hello everyone,

It has been a while since I started what was supposed to be a series focused on tennis analysis from a sports betting perspective. In my first [post](https://www.reddit.com/r/algobetting/comments/ujmpv7/tennis_analysis/), I gave some insights into my motivation and an overview of my data. I also discussed two topics, Implied vs. Realized Probability in tennis betting and O/U Game Lines (theory vs. reality). Moreover, I conducted some backtests based on very simple strategies.

&amp;#x200B;

* Background

My goal for the future is to post more frequently and thereby give you all some trading ideas and valuable insights into tennis analytics. I will typically start with some theory, derived statistics and eventually show some real world betting strategies based on the findings. Whether they would be profitable or not is irrelevant, as both can provide important insights. A bad bet not taken is probably equally valuable as a good bet.

&amp;#x200B;

* Data

For this article, I am only looking at men’s results in official matches for which I have a minimum threshold of data required for the research. My dataset has been growing rapidly recently, since all tournaments have started to resume from the COVID break. Overall, 2022 saw a similar amount of matches as 2016-2019 did (roughly 30000 with clean data) and 2023 is on track to match that. It is important to note that both the quality and quantity of data increased steadily, with more than 60% of the high quality data coming from years &gt;2015.

&amp;#x200B;

* Surprising Outcomes

Today I want to look at upset victories/wins. My definition of an upset is based on bookmaker odds, not on ranking or any other statistics. Bookmaker odds reflect the best guess for the outcome of a match in an efficient market, since they not only take into account the ranking of the two players or their form, but also factors such as the surface, head to head outcomes between the two players and more. Therefore, an upset win can be defined as a win of a player with odds greater than a threshold, let’s say 3 (= Implied Probability roughly 30%, adjusted for vig). 

Firstly, I filter the data to only include players with at least 20 completed matches. Secondly, I exclude players with less than 5 upset wins. Then I start with looking at upset wins with a threshold odd of 3, so every win of a player with odds &gt;3 qualifies as upset win. Since surprises tend to scale with matches played, I rank the outcome by the percentage of upset wins to total matches the player entered as an underdog with odds &gt;3.

Most players making the top 50 of that statistics are ‘newer’ players. This has to do with the fact that most of the high quality data is from recent years, as explained in the Data section. Thus, upset wins from players like Novak Djokovic or Roger Federer are very unlikely, since the data is mainly from a time when they were entering almost every match as a favorite and if they were an underdog, it was typically not with odds &gt;3. 

It is straightforward to see that upset victories typically come at the early stages of the career of a tennis player. That is, when the bookmakers do not have enough information about a players skill. Once they have made some surprising wins, bookmakers lower the odds of the player in subsequent matches to reflect the updated information about their skill level more accurately. Their next wins may therefore not qualify as upset wins anymore, since the odds can be significantly lower than the threshold. This becomes obvious when looking at the odds history of a player like Carlos Alcaraz.

[Graph 1: Carlos Alcaraz ranking vs rolling median odds with a window length of 25 matches.](https://preview.redd.it/k4ugps6iyjoa1.png?width=432&amp;format=png&amp;auto=webp&amp;v=enabled&amp;s=ad92a53e46c91a5f801f8693b075dde24a266b77)

In this graph, the median odds with a rolling window of 25 matches are used. This has the advantage that the curve is smooth and a trend can be easily spotted. Median odds are used instead of average, since the average can plateau on a high level due to one match against a top opponent, for instance Nadal in the French Opens, with very high odds.

In his early days in 2019, when he was first competing in challengers and mainly futures, he often was the underdog. After quick initial success, however, he mainly entered futures tournament matches as the favorite. The same happened in challenger matches in 2020, when he dominated almost every tournament he entered. In 2021, he shifted focus to main tour events, where he often was the underdog. This is where his median odds increase again. In 2022 he had some great victories in the main tour, thus his odds decreased and are now among the lowest of all players, making him the favorite in almost any matchup.

In the following graph, we follow a simple strategy: bet 1 unit on Alcaraz whenever the odds are &gt;3. Obviously, this is with a good portion of hindsight and not a f

[... truncated, see original post ...]

**Top Comments:**

> **u/zahaha** (1 pts): As someone who just got into modeling Woman's Tennis, these are amazing. Please keep it up!

You ever look at live betting trends? Im sure its very hard to get the historical live lines but im curious if there are any situations when "if the pre match odds are &gt;-200 and the live line gets to +300, always take it", or stuff like that.
>

---

### [Where do you get football data for your algos?](https://reddit.com/r/algobetting/comments/1fiesm2/where_do_you_get_football_data_for_your_algos/)
**Author**: u/Thelimegreenishcoder | **Score**: 9 | **Comments**: 6 | **Date**: 2024-09-16

I've been scraping data from FlashFootball.com for the past year for my football predictions algo. However, the website frequently changes, causing my data API to break and requiring constant fixes. With school becoming more demanding, I no longer have the time to manage these issues. Where do you source football(soccer) data for your algorithms or models and do you have any recommendations for reliable alternatives?


I also have always wondered where does Flashfootball.com itself get the data?

**Top Comments:**

> **u/Low_Performance826** (1 pts): write me a dm i will send you a link
>
> **u/atanstef** (1 pts): Hey, I would need historical odds for football matches, where I can obtain them?
>
> **u/chiseeger** (1 pts): Missed the flashfootball part my bad. Mine was American football
>
> **u/chiseeger** (1 pts): Are you doing soccer or American football? I’ve set my own scraper up several times that will move it to your own sql db. Dm me if you’d be interested. I could probably spin it back up
>
> **u/Low_Performance826** (1 pts): if you need historical odds for soccer matches, we have nearly the same coverage as flashscore. If it is just historical odds, we could provide them for free.
>
> **u/soccer-ai** (1 pts): I've been in a similar situation myself. I've been scraping soccer data for about 3 years now and accumulated around 30,000 matches along with historical odds. The constant changes in websites like FlashFootball.com are definitely one of the downsides of relying on scraping. It's a lot of maintenance work.

In terms of alternatives, you could consider paid data sources. While they come with a cost, they can save you the trouble of frequent API breakdowns and constant scraping fixes. Platforms like Opta or SportRadar are commonly recommended, but again, they’re not cheap.

Another interesting approach is using LLM scraping—basically fetching the entire HTML and then using language models to extract the specific data you need via a prompt. It's a more flexible method, but the cost will depend on how many pages you're scraping and the size of your budget.

As for FlashFootball.com, my guess is they either use official data providers or have their own direct sources through partnerships. It’s hard to know for sure so.
>

---

### [Soccer Value Betting Team](https://reddit.com/r/algobetting/comments/120mki5/soccer_value_betting_team/)
**Author**: u/AssignmentHelpful | **Score**: 8 | **Comments**: 8 | **Date**: 2023-03-24

Hey pals, I’m looking to build a small team (3-5 people) to develop a system to price the following soccer markets: moneyline, over/unders and Asian handicaps. 

I recognize the difficulty in pricing soccer given the popularity of the sport, the high cost of data and the competition from big betting syndicates, but I believe there are pricing inefficiencies that we can exploit using feature engineering on event data. The development of the infrastructure will most likely take between 5-10 months with the right people. I have already tackled some of the scrapping and data wrangling required, but I’m still far from having a streamlined system.

The project will entail:
- Scrapping and cleaning event data (started)
- Scrapping and cleaning odds data (started)
- xG, xThreat model implementations (started)
- Feature engineering 
- Developing machine learning modes
- Testing accuracy of the models
- Deploying everything to servers/cloud

This should be a fairly big project, so I don’t expect many of you to be interested. 
The worst case scenario is that we don’t find any edge, if that’s the case we would still have the infrastructure to do any other projects regarding soccer. 

Let me know if you are interested or if you are just curious about the project and it intricacies.

PD: I’m coding in python and storing data in SQL

**Top Comments:**

> **u/TheBigLT77** (1 pts): New to algo but ten years betting on soccer and played at a high level. Happy to help
>
> **u/yungreseller** (1 pts): I’d recommend a different sport, if you print the premium free pinnacle odds against the odds implied by results, you usually find that if there are mispricings they are usually covered by the bookies premium. I mean think about it, in this market alpha can only exist for you, if you are the only one knowing it.
>
> **u/AssignmentHelpful** (1 pts): The idea would be to develop models that beat the closing line on sharp bookmakers (pinnacle and betcris), so that you can consistently bet sizeable amounts on these sites without the danger of getting restricted or banned. Way easier said than done, but I’m certain that it’s achievable on some markets.
>
> **u/boardsteak** (1 pts): How do you expect to capitalize on your results?
>

---

### [Distribution of Poisson : statistical prediction of scores](https://reddit.com/r/algobetting/comments/v33slu/distribution_of_poisson_statistical_prediction_of/)
**Author**: u/kassio92 | **Score**: 6 | **Comments**: 5 | **Date**: 2022-06-02

I have been working on a quantitative model using the Poisson distribution to calculate the probabilities of the scores of soccer games. This law of probabilities is used with historical data (average goal scored by team…).

Need some advices to make it more user-friendly.

[https://www.scorepredict.fr](https://www.scorepredict.fr)

**Top Comments:**

> **u/kassio92** (3 pts): Statistical pronostics 03/06/2022 :

France 2-1 Danemark Probability 8.68% ✅

Croatie 2-1 Autriche Probability 9.08% ✅

Belgique 1-1 Pays-Bas Probability 13.02% ✅✅

If you want to make your own statistical pronostic : https://www.scorepredict.fr
>
> **u/kassio92** (2 pts): Statistical pronostics 07/06/2022 :

Germany 2-1 England Probability : 9.65 %

Italia 1-1 Hungary Probability : 12.46 %

If you want to make your own statistical pronostic : https://www.scorepredict.fr
>
> **u/kassio92** (1 pts): https://plotly.com/python/heatmaps/
>
> **u/kassio92** (1 pts): It’s from plotly, you can also use seaborn
>
> **u/zoidbergisawesome** (1 pts): What are you using for heatmap? Which python lib?
>

---

### [Moving past the Basics (EPL)](https://reddit.com/r/algobetting/comments/psbvxy/moving_past_the_basics_epl/)
**Author**: u/ProdigyManlet | **Score**: 6 | **Comments**: 12 | **Date**: 2021-09-21

Hi everyone, I'm looking at creating an algorithm that predicts the outcome of EPL matches and provides the odds for value-seeking (seems the easiest place to start given the popularity and availability of data). The introductory approach seems to be modelling the expected goals scored by both teams using a Poisson distribution, which is a nice and intuitive model to start with (at least for someone with a bit of an applied stats background).

I'm now looking into more advanced classification methods that predict the outcome of a match between two teams. So far my classification model is getting 50% accuracy using only historical match result data (slightly transformed), so hopefully that's a good starting point. I've got some ideas for more features to add from reading a few papers and some intuition (e.g. manager data, weather, etc.), but was wondering what others found was effective or if they had any lessons learned in moving forward on the modelling side?

This might be too open ended, but some common themes and areas of interest I thought my be relevant to others are:

* How were people's experience with tmproving the basic models (e.g. Poisson) versus moving to classification models (e.g. traditional machine learning)?
* Aside from train/val/test data splits &amp; backtesting, what other techniques did people find effective for evaluating the accuracy or the reliability of their algorithm?
* Did anyone find any common misconceptions? (E.g. chasing down weather data only to find it's impact on model performance was limited).
* Any general types of data aside from match results/historical goal performance that were found useful?

**Top Comments:**

> **u/Davidweb1337** (3 pts): Im not experienced with running models or machine learning so i don't know what kind of data you're looking for. But from what I've heard in the industry, it's been very difficult to find live data feeds for League of legends, especially in China since the organisation running the tournaments over there are apparently not selling any live feeds to betting companies, often leading to latency issues and poor trading on the bookmaker's side. It's usually an esports trader manually adjusting odds while watching the stream haha. Or no live betting offered.

From what I could find, someone has already attempted to build a model here: (includes a link to a dataset, under downloads &amp; tools) https://www.quantumsportssolutions.com/blogs/league-of-legends/a-predictive-model-of-league-of-legends-game-outcomes
>
> **u/lequanghai** (2 pts): Where do you get data for esports? I mostly play and follow League of legends but cant find any complete dataset or source to perform analysis &amp; live betting.
>
> **u/Davidweb1337** (2 pts): E-sports is quite inefficient actually. It has only really started ramping up in the past few years but is still dwarfed by most traditional sports so bookmakers don't really invest as much into R&amp;D for it. You're very likely to find stale prices/lines here, but also very low betting limits.
>
> **u/bananarepubliccat** (2 pts): Yes,  most of the things you mention perform pretty poorly in reality.

Rolling window methods aren't that useful. You want to use season data with possibly priors from the previous season. Again, it is how information gets incorporated. With filter models, the update cycle is capturing all the right information...with rolling windows, you are getting some approximation of skill using unimportant information (against weak opponents, very old matches, etc.). You can weight more recent matches but it still won't beat ELO.

Btw, I didn't make this totally clear in my previous comment: the reason why these sports are hard to model is because the data is adversarial. The information comes from interactions between two teams, it is not only team skill but opponent skill that matters. This is particularly bad in football because you can have teams that win by doing things that would cause other teams to lose (this is less common in other invasion sports where there is usually a dominant strategy)...for example, if you have a model based on possession, teams that counter-attack will be rated poorly...and even then, that counter-attack strategy may only work against certain kinds of teams. And then you have a difference between offensive and defensive strategies: for example, Newcastle always used to outperform vs good teams because they were so defensively solid, but lost it whenever they had to attack the other team. It is very tricky. So an ELO model that has far less data will outperform because the ratings and difference of ratings capture the maximum amount of information.

If you are able to use some non-parametric grouping and then incorporate that into your rating then I think you would be able to produce a more traditional ML model that works (i.e. this team is a counterattack team against an attacking team so we expect X fast breaks, and they got X+5 so we increase their rating)...but even then, I still think the update cycle of filter models like ELO is very effe [...]
>
> **u/king-chungus** (2 pts): Don’t do deep learning, but I definitely think log regression, SVMs, etc… can be viable
>
> **u/ProdigyManlet** (2 pts): Thanks for the extremely detailed reply, this is absolutely awesome and is riddled with great info that answers a whole bunch of my questions (and some I hadn't even thought of yet).

By classification and traditional machine learning I'm referring to things like logistic regression, decision trees/random forest, support vector machines, etc. Basically traditional machine learning is non-deep learning methods. I definitely think Deep Learning would perform pretty poorly in most betting algos given the small data quantities.

In terms of data, I was using a rolling window (e.g. N games like you mentioned) that rolled across prior seasons to avoid the issue of say if N = 20, but we're at match 5 then there's only 4 data points. Obviously a lot changes between seasons which is not accounted for, but I was hoping to factor in information that captured these changes later on (i.e. manager changes/metrics and some form of player metrics). The Brier score looks good, and I like the idea of the ELO approach as it's much more manageable, simple and looks like it will be less reliant on across-season data; will look into all of these.

I had a feeling that the bigger markets will be more difficult. I will still try to get my basic model framework up and running using EPL, and then switch to some local leagues in my own country (looks like I can get the same data in basically the same format so should be an easy switch). I wanted to stick with a sport I have good domain knowledge in as I want to keep it interesting as a hobby while reviewing my classical statistics knowledge (I'm experienced in Deep Learning and Traditional ML, but it's been a while since I went back to the basics of distributions). However, I'll definitely take the suggestion onboard and look at some more obscure markets on the side. I was thinking of E-Sports but I would assume that might be quite efficient too.
>
> **u/TraptInaCommentFctry** (1 pts): &gt;you only update when you see something unexpected, the whole measure is weighted against peers

could you clarify what you mean by this?
>
> **u/bananarepubliccat** (1 pts): That isn't what I said.

I have used data that costs $100k+ annually, the features don't matter if you start from the wrong place (I explained this above, if you are seeing similar predictive power from ELO as ML then you have gone very wrong because ML, as most people are doing it, doesn't work...tbf, most people don't do ELO right either but that isn't a problem with the model). This varies by sport but the OP asked about soccer.

Using ELO as a feature is a basic error (and again, you are missing the point massively). ELO is just a filter, so you can use your ML model as an input to ELO: it is just a map from joint distribution of skill to prediction for a feature, so you can use ML as an input to ELO (I wouldn't advise building a mixture with ELO either, that is a very bad idea practically for soccer because of lineup changes).

How you do this is more complex but the key is that you are modelling a joint probability, that is where the power comes from. What OP will have tried is: X feature over N games or something similar, these models don't work (you can modify features, but it still won't get close). You can get them into a joint probability but, again, the problem is that they don't represent information correctly (again, this is obvious when you think carefully about what you are actually modelling...most people, inadvertently, end up with a single distribution for the average team...this works particularly poorly in soccer where there is no strategic equilibrium i.e. the meaning of features varies hugely based on the team).
>
> **u/MathMod3ler** (1 pts): Thanks for clarifying the original comment. Respectfully, I disagree that traditional ML is incapable of handling that amount of information. I think it comes down to having good features. Although, in practice I prefer using several ELO models as features in my ML models. So I definitely like the information ELO captures.
>
> **u/MathMod3ler** (1 pts): I disagree with a lot of this thread. Although, I think reasonable minds can disagree on this sort of stuff. I would say a couple things to take your modelling to the next level:

1)Stack uncorrelated models.
2) Use the betting market as a starting point for some of your models. The betting market is already a damn good model. Build on top of it, it already takes into account many of the basic features (probably including Poisson Distribution of goals). 
3) Come up with different targets. Ex: Win-Loss Binary and Difference in goals (they both tell you the betting outcome but the computer will look at them very differently).
4) Have way bigger test-validation sets than the normal rules of thumb. Finding patterns is easy...finding persistent patterns is hard.

My two cents, classification is fine. Just really do a lot of safe-guards and validation.
>

---

### [Exploring In-Game Predictions with Odds Data – Would like to Collaborate](https://reddit.com/r/algobetting/comments/1hni8vu/exploring_ingame_predictions_with_odds_data_would/)
**Author**: u/97wschultz | **Score**: 3 | **Comments**: 2 | **Date**: 2024-12-27

Hi everyone,

I’ve been working on a project where I collect odds data at 40-second intervals for EPL and Championship matches, with the goal of exploring whether in-game predictions can be made using this data alone.

I’ve had some promising results so far with models like XGBoost and logistic regression, but there’s plenty of room to build on this. My main focus is on expanding the models and gaining a deeper understanding of the possibilities.

This is more about learning and experimentation than making money. If anyone is interested in getting involved or exchanging ideas, I’d love to collaborate and see where this could lead!

---

### [Looking for a good pre match odds api for soccer](https://reddit.com/r/algobetting/comments/1k65m3u/looking_for_a_good_pre_match_odds_api_for_soccer/)
**Author**: u/Strong_Plant_4545 | **Score**: 2 | **Comments**: 7 | **Date**: 2025-04-23

Hey

I am looking for a reliable odds api for pre match odds for soccer. I need one that is frequently updated and includes many bookmakers from EU. Do you know any and do you know the prices?

---

## Props & Totals

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [NFL Play by Play Data](https://reddit.com/r/algobetting/comments/zlf6xu/nfl_play_by_play_data/)
**Author**: u/mxx24 | **Score**: 7 | **Comments**: 2 | **Date**: 2022-12-14

I've been looking for some more advanced play by play data for a new system, NFL fastr and its python equivalent have personnel and men in box frequencies, but I am looking for something containing the specific man, zone, and type of zone (2-high shell for example) for each play as well.   I've seen various users tout these percentages on Twitter, but cannot find a proper dataset to show for it. thanks.

Edit: I also build out various quant betting models for other sports, have been working on football as of late, happy to partner up if interested

**Top Comments:**

> **u/Louisville117** (1 pts): I tried for a while to see if AWS offered any of its data but sadly no. Would be great even if I had to pay for it. Tons of data in there.
>

---

### [Programmer looking to get started](https://reddit.com/r/algobetting/comments/1gaitzp/programmer_looking_to_get_started/)
**Author**: u/racerx1036 | **Score**: 5 | **Comments**: 4 | **Date**: 2024-10-23

I am a programmer by profession but want to get into algo betting. I work with PHP by way of trade, but have dabbled in python before would definitely need to learn some stuff there as I go though. Whats the best way to get started building an algo im thinking of starting with NBA stats since they seem to be relatively predictable and reliable. I figure doing Overall game stats would be easier to start than including player props like ppg etc but I do want those down the line. I want to as I learn more be able to build this into quite a complex model. What is a good starting point / places to research or watch, first kind of model to build etc. So for NBA what would be some principals to learn to build this model. Any tips appreciated. Thanks!

**Top Comments:**

> **u/Governmentmoney** (1 pts): There are many ways to do things, if you're going down the ML route you can get some ideas from here: [https://betfair-datascientists.github.io/modelling/howToModel/](https://betfair-datascientists.github.io/modelling/howToModel/)

Pretty basic stuff but it will give you a direction to move towards and experiment
>
> **u/__sharpsresearch__** (1 pts): nba_api is was faster than scraping. it will save you days.

pandas/sklearn/numpy should be all you need on the modeling front for the most part

decision trees are very common, our model that is currently running on our site is using a light gradient boosted tree
>
> **u/racerx1036** (1 pts): Thinking of just web scraping something and playing around with pandas and decision trees but not really sure what to do there so I’ll have to do some researching. But yeah like u say to start simple but when I’m ready for more what direction do I head?
>
> **u/__sharpsresearch__** (1 pts): good picks on nba, high level team stats btw.


nba_api is great. join their slack.

initially, make a db, grab everything from ~2008-2010 and throw it in a team, player, match, boxscore table. or something similar so you can fuck around and not get rate limited.
>

---

### [How useful is something like this](https://reddit.com/r/algobetting/comments/1k662a4/how_useful_is_something_like_this/)
**Author**: u/Forsaken-Hearing3540 | **Score**: 4 | **Comments**: 17 | **Date**: 2025-04-23

www.playerprobabilities.com

I’ve been working on a machine learning model to predict NBA player props — specifically points, assists, and rebounds. Originally, I used linear regression (with Lasso for feature selection) and rolling averages to predict raw values. That alone gave me around 57  - 70% accuracy on some given days, this is for 68+ players on game days.

Now I’ve taken it a step further:
I treat the regression prediction as a mean,
Calculate a confidence interval using a z-score (95% confidence),
Run Monte Carlo simulations to estimate the distribution of outcomes,
Then compute the probability a player hits the over/under line.

Also a second reason why I am here ,can you guys share any tips on how you guys account for lineup changes and how it affects what a player is going to score. I have really been struggling with that aspect of things.l

---

### [NBA player prop stats scraping](https://reddit.com/r/algobetting/comments/13w2no6/nba_player_prop_stats_scraping/)
**Author**: u/fiachrah98 | **Score**: 4 | **Comments**: 4 | **Date**: 2023-05-30

Hi,
I’ve been running a player prop betting system for NBA since start of conference finals but it consists of me going to different websites and copying and pasting info every day.

These are the website I need a way of extracting the table from into a google sheet.

Any help is appreciated.

https://www.nba.com/stats/players/traditional?PerMode=Totals&amp;LastNGames=5

https://www.lineups.com/nba/nba-player-minutes-per-game

System after conference finals:

Bets: 121
Profit: 22.71u
ROI: 14.6%

---

### [Beating books on NBA Props](https://reddit.com/r/algobetting/comments/1kf2o9j/beating_books_on_nba_props/)
**Author**: u/Consistent_Buy625 | **Score**: 3 | **Comments**: 1 | **Date**: 2025-05-05

I’ve been testing a few different models against NBA player props (points, assist, rebounds) to see how they compare to sportsbooks. I’ve been using things like the way back machine on rotowire to obtain large amounts of previous props at once. I’m wondering if it’s worth also testing across playoff seasons to see if there is any variance due to playoff performance from players being different than the regular season, and also how much of an edge I would need in order to break even/become profitable

---

### [How sharp really is FanDuel on NBA props?](https://reddit.com/r/algobetting/comments/1keycjh/how_sharp_really_is_fanduel_on_nba_props/)
**Author**: u/jcmmania | **Score**: 3 | **Comments**: 4 | **Date**: 2025-05-05

I have heard through the grapevine multiple times that FanDuel is sharp on NBA player props. For this reason, as a top-down bettor I’ve been avoiding betting NBA player props into Fanduel, even when they diverge significantly from the rest of the market including actually sharp books like Pinnacle. Am I overrating Fanduel in this regard? Also, how does time from tip-off play into this (i.e. does Pinnacle’s edge over Fanduel increase as they take more sharp action on a given game)?

---

### [Underdog NFL +EV Record by Week](https://reddit.com/r/algobetting/comments/1iolda6/underdog_nfl_ev_record_by_week/)
**Author**: u/FavoredProps | **Score**: 2 | **Comments**: 0 | **Date**: 2025-02-13

**What’s up! We graphed the hit rate for props identified as +EV on the Underdog DFS site for the 2024 NFL Regular Season.** 



**Approach:**

⁃    Included standard-payout props with -125 or better average odds from 4+ sportsbooks

⁃    Props with line changes were considered separate props

⁃    Since we had 15 minute snapshots of data, the last occurrence of a prop was used to prevent duplicates



The **overall hit rate for the regular season was 54.6%** over 3601 props that were included in the approach above. For context, the **breakeven hit rate for each pick in a 6-leg flex parlay is 53.8%.** 



**Also, “Under” +EV props are more accurate and made up just 40% of the total count.**

⁃    Over: 53.9%

⁃    Under: 55.7%



It seems like blindly tailing +EV plays this season would’ve earned a small profit. To help get those numbers up, we made a Free Player Prop Tool [https://www.favoredprops.com/dfs/nba](https://www.favoredprops.com/dfs/nba) to research more data points like defensive rankings, line movement, and hit-rate in various situations



**Let us know if you’d like to see more content like this!**

https://preview.redd.it/553omucibxie1.jpg?width=1440&amp;format=pjpg&amp;auto=webp&amp;s=858e96555ef6bd79da1384c5d62ee3dc61b38483

---

### [Closing lines from yesterday??](https://reddit.com/r/algobetting/comments/1fpzudx/closing_lines_from_yesterday/)
**Author**: u/Old-Pie-9913 | **Score**: 2 | **Comments**: 3 | **Date**: 2024-09-26

Yo! Does anyone know where you can see yesterday's closing lines across sharp books? Pinny, Cris, Circa, etc.? I'm able to find main markets but am looking for props. So far no luck...anyone know where I can find historical prop lines? THANKS!

---

## Account Limits & Sportsbook Issues

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [Tennis Analysis #2: Upset Victories](https://reddit.com/r/algobetting/comments/11v0289/tennis_analysis_2_upset_victories/)
**Author**: u/quant_boy123 | **Score**: 12 | **Comments**: 1 | **Date**: 2023-03-18

Hello everyone,

It has been a while since I started what was supposed to be a series focused on tennis analysis from a sports betting perspective. In my first [post](https://www.reddit.com/r/algobetting/comments/ujmpv7/tennis_analysis/), I gave some insights into my motivation and an overview of my data. I also discussed two topics, Implied vs. Realized Probability in tennis betting and O/U Game Lines (theory vs. reality). Moreover, I conducted some backtests based on very simple strategies.

&amp;#x200B;

* Background

My goal for the future is to post more frequently and thereby give you all some trading ideas and valuable insights into tennis analytics. I will typically start with some theory, derived statistics and eventually show some real world betting strategies based on the findings. Whether they would be profitable or not is irrelevant, as both can provide important insights. A bad bet not taken is probably equally valuable as a good bet.

&amp;#x200B;

* Data

For this article, I am only looking at men’s results in official matches for which I have a minimum threshold of data required for the research. My dataset has been growing rapidly recently, since all tournaments have started to resume from the COVID break. Overall, 2022 saw a similar amount of matches as 2016-2019 did (roughly 30000 with clean data) and 2023 is on track to match that. It is important to note that both the quality and quantity of data increased steadily, with more than 60% of the high quality data coming from years &gt;2015.

&amp;#x200B;

* Surprising Outcomes

Today I want to look at upset victories/wins. My definition of an upset is based on bookmaker odds, not on ranking or any other statistics. Bookmaker odds reflect the best guess for the outcome of a match in an efficient market, since they not only take into account the ranking of the two players or their form, but also factors such as the surface, head to head outcomes between the two players and more. Therefore, an upset win can be defined as a win of a player with odds greater than a threshold, let’s say 3 (= Implied Probability roughly 30%, adjusted for vig). 

Firstly, I filter the data to only include players with at least 20 completed matches. Secondly, I exclude players with less than 5 upset wins. Then I start with looking at upset wins with a threshold odd of 3, so every win of a player with odds &gt;3 qualifies as upset win. Since surprises tend to scale with matches played, I rank the outcome by the percentage of upset wins to total matches the player entered as an underdog with odds &gt;3.

Most players making the top 50 of that statistics are ‘newer’ players. This has to do with the fact that most of the high quality data is from recent years, as explained in the Data section. Thus, upset wins from players like Novak Djokovic or Roger Federer are very unlikely, since the data is mainly from a time when they were entering almost every match as a favorite and if they were an underdog, it was typically not with odds &gt;3. 

It is straightforward to see that upset victories typically come at the early stages of the career of a tennis player. That is, when the bookmakers do not have enough information about a players skill. Once they have made some surprising wins, bookmakers lower the odds of the player in subsequent matches to reflect the updated information about their skill level more accurately. Their next wins may therefore not qualify as upset wins anymore, since the odds can be significantly lower than the threshold. This becomes obvious when looking at the odds history of a player like Carlos Alcaraz.

[Graph 1: Carlos Alcaraz ranking vs rolling median odds with a window length of 25 matches.](https://preview.redd.it/k4ugps6iyjoa1.png?width=432&amp;format=png&amp;auto=webp&amp;v=enabled&amp;s=ad92a53e46c91a5f801f8693b075dde24a266b77)

In this graph, the median odds with a rolling window of 25 matches are used. This has the advantage that the curve is smooth and a trend can be easily spotted. Median odds are used instead of average, since the average can plateau on a high level due to one match against a top opponent, for instance Nadal in the French Opens, with very high odds.

In his early days in 2019, when he was first competing in challengers and mainly futures, he often was the underdog. After quick initial success, however, he mainly entered futures tournament matches as the favorite. The same happened in challenger matches in 2020, when he dominated almost every tournament he entered. In 2021, he shifted focus to main tour events, where he often was the underdog. This is where his median odds increase again. In 2022 he had some great victories in the main tour, thus his odds decreased and are now among the lowest of all players, making him the favorite in almost any matchup.

In the following graph, we follow a simple strategy: bet 1 unit on Alcaraz whenever the odds are &gt;3. Obviously, this is with a good portion of hindsight and not a f

[... truncated, see original post ...]

**Top Comments:**

> **u/zahaha** (1 pts): As someone who just got into modeling Woman's Tennis, these are amazing. Please keep it up!

You ever look at live betting trends? Im sure its very hard to get the historical live lines but im curious if there are any situations when "if the pre match odds are &gt;-200 and the live line gets to +300, always take it", or stuff like that.
>

---

### [The benefit of new coding methods in AI for peoples with limited skills in programing. A journey to get your data for sports betting analysis.](https://reddit.com/r/algobetting/comments/1j9n0ri/the_benefit_of_new_coding_methods_in_ai_for/)
**Author**: u/schnapo | **Score**: 7 | **Comments**: 0 | **Date**: 2025-03-12

I recently tackled a personal project to scrape a large set of sports data from a website—thousands of lines’ worth—and transform it into a format I could analyze. Normally, I’d spend days or even weeks juggling various scripts and debugging each step. But this time, I brought AI into the mix, and it made a world of difference. Here’s a quick overview of the process, without going into the nitty-gritty of the actual code:

I outlined my goals to an AI assistant: gather data on games, teams, and statistics from a particular sports site. The AI helped me piece together a basic approach—where to send requests, how to parse the pages, and what columns I might need.

Once I had a rudimentary script, I hit typical obstacles like missing data fields, date mismatches, and odd formatting. Each time I encountered a snag, I described the issue to the AI and got suggestions on how to fix or streamline the process. It was like having a coding partner who never sleeps.

After a few rounds of refinement, I could easily loop through a range of dates and collect thousands of lines of game data in a fraction of the time it would normally take. The AI offered best practices along the way—like how to handle inconsistent naming conventions and how to merge data sets without losing rows.

In just a few hours, I had a robust data set ready for analysis. Where I might normally spend days doing trial-and-error debugging, I now had a near-automated pipeline. It was a massive time-saver and a huge motivator to tackle more complex data tasks in the future.

  
If you’re thinking about diving into web scraping or data collection, consider bringing AI assistance into the process. It won’t do all the thinking for you, but it can drastically cut down on the time you spend wrestling with small, repetitive hurdles. It’s a perfect way to focus on the bigger picture—like deciding how to use all the data you’re collecting—rather than getting stuck on every little detail of the code.

  
For example: I have never worked with Python before, only with R. Now I have a full scraper ready which captures lines, ratings and data within minutes. It is not something to brag, just motivate others to do the extra work.

---

### [Moving past the Basics (EPL)](https://reddit.com/r/algobetting/comments/psbvxy/moving_past_the_basics_epl/)
**Author**: u/ProdigyManlet | **Score**: 6 | **Comments**: 12 | **Date**: 2021-09-21

Hi everyone, I'm looking at creating an algorithm that predicts the outcome of EPL matches and provides the odds for value-seeking (seems the easiest place to start given the popularity and availability of data). The introductory approach seems to be modelling the expected goals scored by both teams using a Poisson distribution, which is a nice and intuitive model to start with (at least for someone with a bit of an applied stats background).

I'm now looking into more advanced classification methods that predict the outcome of a match between two teams. So far my classification model is getting 50% accuracy using only historical match result data (slightly transformed), so hopefully that's a good starting point. I've got some ideas for more features to add from reading a few papers and some intuition (e.g. manager data, weather, etc.), but was wondering what others found was effective or if they had any lessons learned in moving forward on the modelling side?

This might be too open ended, but some common themes and areas of interest I thought my be relevant to others are:

* How were people's experience with tmproving the basic models (e.g. Poisson) versus moving to classification models (e.g. traditional machine learning)?
* Aside from train/val/test data splits &amp; backtesting, what other techniques did people find effective for evaluating the accuracy or the reliability of their algorithm?
* Did anyone find any common misconceptions? (E.g. chasing down weather data only to find it's impact on model performance was limited).
* Any general types of data aside from match results/historical goal performance that were found useful?

**Top Comments:**

> **u/Davidweb1337** (3 pts): Im not experienced with running models or machine learning so i don't know what kind of data you're looking for. But from what I've heard in the industry, it's been very difficult to find live data feeds for League of legends, especially in China since the organisation running the tournaments over there are apparently not selling any live feeds to betting companies, often leading to latency issues and poor trading on the bookmaker's side. It's usually an esports trader manually adjusting odds while watching the stream haha. Or no live betting offered.

From what I could find, someone has already attempted to build a model here: (includes a link to a dataset, under downloads &amp; tools) https://www.quantumsportssolutions.com/blogs/league-of-legends/a-predictive-model-of-league-of-legends-game-outcomes
>
> **u/lequanghai** (2 pts): Where do you get data for esports? I mostly play and follow League of legends but cant find any complete dataset or source to perform analysis &amp; live betting.
>
> **u/Davidweb1337** (2 pts): E-sports is quite inefficient actually. It has only really started ramping up in the past few years but is still dwarfed by most traditional sports so bookmakers don't really invest as much into R&amp;D for it. You're very likely to find stale prices/lines here, but also very low betting limits.
>
> **u/bananarepubliccat** (2 pts): Yes,  most of the things you mention perform pretty poorly in reality.

Rolling window methods aren't that useful. You want to use season data with possibly priors from the previous season. Again, it is how information gets incorporated. With filter models, the update cycle is capturing all the right information...with rolling windows, you are getting some approximation of skill using unimportant information (against weak opponents, very old matches, etc.). You can weight more recent matches but it still won't beat ELO.

Btw, I didn't make this totally clear in my previous comment: the reason why these sports are hard to model is because the data is adversarial. The information comes from interactions between two teams, it is not only team skill but opponent skill that matters. This is particularly bad in football because you can have teams that win by doing things that would cause other teams to lose (this is less common in other invasion sports where there is usually a dominant strategy)...for example, if you have a model based on possession, teams that counter-attack will be rated poorly...and even then, that counter-attack strategy may only work against certain kinds of teams. And then you have a difference between offensive and defensive strategies: for example, Newcastle always used to outperform vs good teams because they were so defensively solid, but lost it whenever they had to attack the other team. It is very tricky. So an ELO model that has far less data will outperform because the ratings and difference of ratings capture the maximum amount of information.

If you are able to use some non-parametric grouping and then incorporate that into your rating then I think you would be able to produce a more traditional ML model that works (i.e. this team is a counterattack team against an attacking team so we expect X fast breaks, and they got X+5 so we increase their rating)...but even then, I still think the update cycle of filter models like ELO is very effe [...]
>
> **u/king-chungus** (2 pts): Don’t do deep learning, but I definitely think log regression, SVMs, etc… can be viable
>
> **u/ProdigyManlet** (2 pts): Thanks for the extremely detailed reply, this is absolutely awesome and is riddled with great info that answers a whole bunch of my questions (and some I hadn't even thought of yet).

By classification and traditional machine learning I'm referring to things like logistic regression, decision trees/random forest, support vector machines, etc. Basically traditional machine learning is non-deep learning methods. I definitely think Deep Learning would perform pretty poorly in most betting algos given the small data quantities.

In terms of data, I was using a rolling window (e.g. N games like you mentioned) that rolled across prior seasons to avoid the issue of say if N = 20, but we're at match 5 then there's only 4 data points. Obviously a lot changes between seasons which is not accounted for, but I was hoping to factor in information that captured these changes later on (i.e. manager changes/metrics and some form of player metrics). The Brier score looks good, and I like the idea of the ELO approach as it's much more manageable, simple and looks like it will be less reliant on across-season data; will look into all of these.

I had a feeling that the bigger markets will be more difficult. I will still try to get my basic model framework up and running using EPL, and then switch to some local leagues in my own country (looks like I can get the same data in basically the same format so should be an easy switch). I wanted to stick with a sport I have good domain knowledge in as I want to keep it interesting as a hobby while reviewing my classical statistics knowledge (I'm experienced in Deep Learning and Traditional ML, but it's been a while since I went back to the basics of distributions). However, I'll definitely take the suggestion onboard and look at some more obscure markets on the side. I was thinking of E-Sports but I would assume that might be quite efficient too.
>
> **u/TraptInaCommentFctry** (1 pts): &gt;you only update when you see something unexpected, the whole measure is weighted against peers

could you clarify what you mean by this?
>
> **u/bananarepubliccat** (1 pts): That isn't what I said.

I have used data that costs $100k+ annually, the features don't matter if you start from the wrong place (I explained this above, if you are seeing similar predictive power from ELO as ML then you have gone very wrong because ML, as most people are doing it, doesn't work...tbf, most people don't do ELO right either but that isn't a problem with the model). This varies by sport but the OP asked about soccer.

Using ELO as a feature is a basic error (and again, you are missing the point massively). ELO is just a filter, so you can use your ML model as an input to ELO: it is just a map from joint distribution of skill to prediction for a feature, so you can use ML as an input to ELO (I wouldn't advise building a mixture with ELO either, that is a very bad idea practically for soccer because of lineup changes).

How you do this is more complex but the key is that you are modelling a joint probability, that is where the power comes from. What OP will have tried is: X feature over N games or something similar, these models don't work (you can modify features, but it still won't get close). You can get them into a joint probability but, again, the problem is that they don't represent information correctly (again, this is obvious when you think carefully about what you are actually modelling...most people, inadvertently, end up with a single distribution for the average team...this works particularly poorly in soccer where there is no strategic equilibrium i.e. the meaning of features varies hugely based on the team).
>
> **u/MathMod3ler** (1 pts): Thanks for clarifying the original comment. Respectfully, I disagree that traditional ML is incapable of handling that amount of information. I think it comes down to having good features. Although, in practice I prefer using several ELO models as features in my ML models. So I definitely like the information ELO captures.
>
> **u/MathMod3ler** (1 pts): I disagree with a lot of this thread. Although, I think reasonable minds can disagree on this sort of stuff. I would say a couple things to take your modelling to the next level:

1)Stack uncorrelated models.
2) Use the betting market as a starting point for some of your models. The betting market is already a damn good model. Build on top of it, it already takes into account many of the basic features (probably including Poisson Distribution of goals). 
3) Come up with different targets. Ex: Win-Loss Binary and Difference in goals (they both tell you the betting outcome but the computer will look at them very differently).
4) Have way bigger test-validation sets than the normal rules of thumb. Finding patterns is easy...finding persistent patterns is hard.

My two cents, classification is fine. Just really do a lot of safe-guards and validation.
>

---

## Betting Exchanges

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [Hi, I'm the founder of Sporttrade, a sports betting exchange in New Jersey.](https://reddit.com/r/algobetting/comments/10pn1ri/hi_im_the_founder_of_sporttrade_a_sports_betting/)
**Author**: u/sporttrade | **Score**: 11 | **Comments**: 29 | **Date**: 2023-01-31

Hi reddit,

My name is Alex Kane, and I'm the founder and ceo of Sporttrade.

Before you read this, yes, this is an ad. But it's not one where we hope to earn a bunch of downloads. Instead, my hope is to connect with some of you directly about our product and how you can use it to your advantage.

**A bit about me**

I started Sporttrade in 2018, before sports betting was legal in New Jersey. I didn't really know much about betting at the time. My goal was to create an app that combined betting and trading.

Sometime in 2019, I figured I would try placing a bet. I had followed Captain Jack on twitter, and he had mentioned something about bonus arbitrage. At that time, there were 15 sportsbooks in NJ, all offering $250+ for new players. So, I paired up with my buddy, a math teacher, and set out to NJ to try and take advantage of the bonuses.

Several trips to new States and a few overdrafts of my checking account later, I felt like I had done well to take advantage of various offers, VIP programs, and learned a lot about the industry.

While the perils of online casino ultimately cost me a few thousand 🙄 , I still came out on top, with my profits topping my Sporttrade salary some years! (Pikkit record attached)

**Arbing signup bonuses**

As many of you know, there's a significant profit opportunity presented by the numerous sign-up offers at books like DK and FD.

In short, it looks like this:

Draftkings offers a $1,000 risk free first bet. If the bet loses, you get a $1,000 bet credit back. So, you place a bet on something like "Giants Moneyline" at 3/1 odds on DK, and then "Eagles Moneyline" at 1/3 odds on Fanduel.

Either way, you win/lose $0, but if the Giants lose, DK gives you a $1000 bet credit. You then place another bet "pair" ($1000 bet credit on DK, and an offsetting bet on Pointsbet) to turn that $1,000 credit into cash.

...then onto the next welcome offer.

**What is Sporttrade?**

As I learned more arb betting, I began to realize how beneficial a betting exchange could be to arbitrage bettors. In fact, some of our biggest customers are doing just that; arbing prices and offers of other venues.

Here are some qualities about Sporttrade that make it a must-have for arbers:

➡️ Really tight pricing (as good as -103/-103 on a 50/50 bet)➡️ Transparent limits, and great liquidity (several thousand $ available)➡️ No delays, and instant re-bets

**My offer to you:**

In talking to many of our customers, I realize that while most folks have taken advantage of DK, FD, MGM, PointsBet, CZR offers, they haven't done the same for Betway, WynnBet, Superbook, etc.

So, if any of you are up for it, I'd be more than happy to set up time to meet, introduce you to Sporttrade, and help you use us to get the most out of your betting, whether you're an arbing beginner, or looking to take your game to the next level. My number is below.

Your first bet on Sporttrade is risk free, up to $300 (so I can help you arb that!), and thanks to our partnership with Unabated and OddsJam, you can get access to those tools at a significant discount.

Thanks for reading, and looking forward to connecting with some of you!

Alex(484) 678-8791

**Edit:** You can download the app here:   
https://apps.apple.com/us/app/sporttrade/id1525381125

&amp;#x200B;

[2021 Pikkit Record \(my last year of arbing\)](https://preview.redd.it/j6gn58gzsafa1.jpg?width=1242&amp;format=pjpg&amp;auto=webp&amp;v=enabled&amp;s=795a6562baf0183c81e9825f8921e0739339050b)

**Top Comments:**

> **u/Ok-Seaworthiness3874** (2 pts): Cool idea, and looks like great execution (sorry I'm not in NJ so I can't check), but do you offer e-sports betting? It is VERY difficult to find US based books (Maybe not any tbh, some have only like Super S tier events only) that offer comprehensive offerings of e-sports (it's basically just bovada which is very grey-market, but legit, and thank god for them). 

Considering the MASSIVE growth in e-sports, and especially appealing to a young demographic that probably isn't into traditional sports typically - would you consider adding it?

I'm a bit of a Dota 2 sharp (game with yearly 40M prize pools for players, shit aint no joke) and am on my probably 10th bovada account. Thinking about moving states because the lack of opportunity to bet is frustrating.
>
> **u/SOGorman35** (2 pts): 1) not really a question but I hate you because I had an idea for an exchange like SportTrade (before I knew anything about sports betting) only to discover that it already existed.  I'm definitely rooting for you to succeed.
2) Ohio anytime soon?
3) I know you have said that there are multiple marker makers lined up, and I wouldn't expect you to necessarily identify them, but are any of the MMs affiliated with SportTrade?  I know that Nadex and Kalshi both have affiliates or subsidiaries that function as the primary MMs in their exchanges, so I'm half assuming this is the case here.
>
> **u/afk_again** (2 pts): This looks interesting.  Are there plans to support horse racing?  Also can you post again when there's API access.  A swagger page would be nice too.
>
> **u/Fly-iggles-fly** (1 pts): Is Spanky one of your market makers?
>
> **u/Artistic_Dog_** (1 pts): Hey Alex, how is this developing? Do you have a trading API or connection to trading software like Bet Angel or GeeksToy? Super interested on this
>
> **u/sporttrade** (1 pts): Now in NJ/CO/IA/AZ/VA, we’d like to launch in:

IN/MD/KY/NC/MI/IL/PA/OH/MO/WV/LA/MA/KS

although some of those states will require some legislative changes
>
> **u/madtadder** (1 pts): I reached out to them directly in February, and they said "We haven’t made available our pricing api to individuals just yet. Once we do that, we fear the floodgates will open and we would need to rebuild our market data endpoint service to handle the load" which is sorta hilarious since they claim to have an API that's available
>
> **u/random-50** (1 pts): Any trading api yet, or imminent?

What’s the pipeline of states?
>
> **u/poubelleaccount** (1 pts): I don't see much liquidity on [https://markets.getsporttrade.com/nj](https://markets.getsporttrade.com/nj); for instance, there doesn't seem to be a market on the Pacers game today. Is that a bug?
>
> **u/OliverAlden** (1 pts): Thanks.  Just discovered sports trade which is new to my state.
>

---

### [Best Algorithmic Market Making Strategy?](https://reddit.com/r/algobetting/comments/1ieed8t/best_algorithmic_market_making_strategy/)
**Author**: u/nvng | **Score**: 7 | **Comments**: 9 | **Date**: 2025-01-31

Most of the content I see on this sub is about building a profitable model to predict the outcome of a match, but whats the best way to make money once we have a good model? Seems that most people are just doing straight EV bets but MM strategies on exchanges sound way more attractive. No limiting/banning, often can bet higher volumes, and some of these exchanges even offer rebates for high volume. 

So what goes into these algorithmic market making strategies? Is it just simple mispricing, i.e. you find a theoretical value and quote the market at a profitable margin? Or is it more complex where people are building advanced hedges and grouping bets to create spreads.

**Top Comments:**

> **u/BetBrotherApp** (1 pts): As a rule of thumb bookmakers always have the most accurate models plus an edge. 

Try to compare prices across a range of bookmakers and look for differences. The research paper “Beating the bookies with their own numbers - and how the online sports betting market is rigged” is a decent paper on this. 

Line movements is incredibly important, as well as placing bets early enough before the odds drop

Lastly looking at psychological factors plays a role, often times markets are mispriced due to overall sentiment not actual data
>
> **u/neverfucks** (1 pts): if you put up a sign that says "i'm willing to sell eagles +1.5 at -105 and buy eagles +1.5 at +105" you are not only a market maker, you're a sportsbook operator and you need a license unless you are doing your market making on an exchange like novig that is legal in your state.
>
> **u/redtwinned** (1 pts): Huh, didnt know you could do that. I live in a state where books aren’t legal but fantasy apps are, so I’m on a friend’s book. Normally he has me generate lines for local games that aren’t offered by his website that he uses. Maybe I should talk to the backers about getting a deal lmao
>
> **u/BowTiedBettor** (1 pts): and some of these exchanges charge hefty fees on profits
>
> **u/neverfucks** (1 pts): market making. you put up a sign that says "i'm willing to buy up to 50 apples from anyone for a dollar and i'm willing to sell up to 50 apples for a dollar 5" and bam you are making a market in apples. if you sell as many apples as you buy, you've done well as a middleman and you make a profit. if people are much more interested in either buying from you or selling to you, you need to move your prices or you will get trucked. welcome to capitalism baby
>
> **u/grammerknewzi** (1 pts): What difference is there between market making and showing two sided lines like a book does? Both are accepting two sided risk for enough edge.
>
> **u/jbet13** (1 pts): It’s called market making, also not necessarily looking for equal volume
>
> **u/ZeltronTheHellspawn** (1 pts): https://preview.redd.it/vrq40qkpcfge1.jpeg?width=250&amp;format=pjpg&amp;auto=webp&amp;s=79a55c13c2e4b775f43bfc3a21ce82dd1a10a20e
>
> **u/grammerknewzi** (1 pts): pretty sure this is just called being a book; your really just scalping odds by hoping you get large, but equal volume on both sides of a spread for example.
>
> **u/jbet13** (1 pts): Don’t think anyone will give away the secrets of this one but just remember 
- adverse selection 
- nice prior price 
- move with money 
- know where high variance price moves may occur
>

---

### [Where does Star Lizard and other large scale betting co’s place its bets?](https://reddit.com/r/algobetting/comments/1kf7vtu/where_does_star_lizard_and_other_large_scale/)
**Author**: u/dtl85 | **Score**: 3 | **Comments**: 3 | **Date**: 2025-05-05

Question as above - most of us are aware of Tony Bloom/Star Lizard/and some of the other large betting co’s, and my question is - where would companies like this place its bets? 

Can’t imagine it’s easy to just drop some potentially huge stakes into Betfair Exchange? Also, it’s a company too - I thought Exchanges only cater for individuals?

---

### [Technical analysis on sports](https://reddit.com/r/algobetting/comments/1k0euwc/technical_analysis_on_sports/)
**Author**: u/Zestyclose-Gur-655 | **Score**: 2 | **Comments**: 0 | **Date**: 2025-04-16

On the stock market technical analysis of charts is very popular. 

Usually bookmakers don't offer any charts at all. (But they don't even want people to win, they barely show you profit and loss because they rather hide people are losing.)  
Some betting exchanges have charts, betinasia also does. 

Does it make sense to use any charts for betting and why not? 

Maybe i'm crazy but i found if i analyse a game, sometimes it's quite obvious where the money is coming in on. Because bookies just keep moving the price on one side. You can basically see it on the chart where people have been betting on. It kind of tells the story of that particular market.

In theory if you have a chart where the odds are constantly dropping, you first back at a good price then later lay it. This creates some value. Or vice versa with odds that are becoming bigger, so less of a % chance. First lay it then back it. 

The problem is maybe events that are going one side don't have to keep going that side. I think it does slightly more often then not but this is just an assumption that i make, i don't have hard data on if steamers more often then not keep steaming. 

I'm just trying to think like a bookie right now, essentially they just back and lay bets with a spread in between. This is similar to market makers, actually it is a form of market making. The real value then to me seems to anticipate where odds are going to, more so then where they are now. This is also true for gamblers, and even gamblers are just trying to beat closing line value, get a better value themselves. This indicates a profitable strategy. So if odds move in your advantage more often then not, this is part of the goal to me it seems. 

Say you was a bookmaker, in essence the best thing for them is have some markets that just go sideways forever with a big spread. They can constantly buy and sell, buy and sell and make a profit. Often you do see that odds move a certain direction. For bookmakers this is somewhat of a loss because their odds where first not correct. This is also why you can only bet little when an event is days away and big when it nears to start. The price has to shape to where it should be. Once everyone made their bets they know pretty good where it should about be priced. 

Maybe i spend too much time on the stock market but i do see also just trends, mean reversions, support and resistance in betting markets. In fact i think betting markets are even way more logical then financial markets. There might also be manipulation by single actors but for a bookie it's not good if odds are much different then where the real odds should be. Mispriced events makes it possible to value bet, since only the outcomes in reality influences the outcome of a bet. On financial markets it's mostly just price alone that has any meaning, fundamentals to a lesser extent. Option contracts are based on the price of the underlying not on the outcome of events. So there is much more what George Soros would call: "reflexivity" possible. Even the market participants itself can influence reality.

---

## MLB / Baseball

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [A tool for analysing odds](https://reddit.com/r/algobetting/comments/yd86kl/a_tool_for_analysing_odds/)
**Author**: u/_rbp_ | **Score**: 13 | **Comments**: 8 | **Date**: 2022-10-25

I have created an application for analysing odds – [www.rationalbets.com](https://www.rationalbets.com). It allows to identify profitable sports bets using the concept of expected value. I would be very grateful if you could check it's handy and provide feedback.

All you have to do to use it is:

· Choose an event from the sidebar or add a custom one.

· Set the probabilities of the event outcomes to your best knowledge using intuitive sliders.

Based on the probability distribution you specify, the tool will calculate the expected profits of your picks.

The tool is regularly updated with odds for football, NFL, baseball, and basketball. There is also an article section on maths in gambling.

www.rationalbets.com

**Top Comments:**

> **u/consolationgoal** (5 pts): It looks like you are using straight probabilities from the bookmaker's odds, meaning that the equation is 1/odds = probability. Right?

That means your probabilities include the bookmaker's margin, which in turn shows the expected net to win as zero. In reality, given bookmaker margins, the expected net to win should start out as negative. After all, that's how they make their money. Only by adjusting the probabilities should you be able to move the expected profit to zero or positive. 

In the Leicester City - Man City example, Pinnacle odds are 10.09 x 6.20 x 1.30. That means the bookmaker margin is 2.9% 

(1/10.09) + (1/6.20) + (1/1.30) = 1.029

So unless a person moves the sliders, it the net expected profit from a 10 euro bet should be -0.29 right?
>
> **u/_rbp_** (3 pts): I think there are a few good arguments against parlays:

1. As good as you might be at predicting events, you can't always get everything right. Losing parlays happens often, as the probability of winning decreases exponentially. For example let's say you place 5 bets, each one with a 90% chance winning (as sure as you can be of an outcome in most cases). The chance of winning a parlay is only 90%\^5 = 59%.
2. Parlays are bets with large odds, but a small probability of a payout. Such types of bets drastically increase the variance of your winnings. In other words, you have a larger chance of winning big, but also a larger chance of loosing big. I actually have a nice simulation of that in my [article on variance](https://www.rationalbets.com/articles/#variance).
3. There's one argument I don't think is necessary true, but probably is very often true - when placing a bet, you are paying the bookmaker his margin. The more bets you place in a parlay, the more this margin will increase (as it multiplies across all your picks).

These arguments aren't just theory - I don't believe any professional bettor would do parlays for the above reasons (unless from time to time for fun).
>
> **u/consolationgoal** (3 pts): Thanks for the explanation. You should check out the below paper, which gives great detail on how best to remove the bookmaker margin (including formulas). As you said, there is no exact certainty on how a given bookmaker does it, but the testing in the below paper makes clear the best option for the public to try to remove the bookmaker margin.

[https://www.football-data.co.uk/The\_Wisdom\_of\_the\_Crowd\_updated.pdf](https://www.football-data.co.uk/The_Wisdom_of_the_Crowd_updated.pdf)

I totally understand the desire to maybe not go crazy on precision, but professional sports bettors are often surviving on 1% edges (especially in the major sports like you've got on this tool), so I think precision is key.

More broadly, who is the target market for the tool? I feel like recreational bettors are unlikely to have a probability (even a reasonable range, frankly) for their desired bet, so they might not be able to take advantage of the tool. They are likely going to just line-shop, which your tool does help with but there are other more established options out there for that (Betstamp, etc). 

Originators - i.e. handicappers who create their own probabilities for an event - will be able to fairly easily determine their projected edge.

I don't really do parlays so I didn't check out that part of things, but it's true those probabilities are less well understood generally so that might be something that draws people's attention.

Looks like a lot of work went into the tool. Great job getting to this place.
>
> **u/Available_Remove452** (3 pts): I'm interested in trying this, thank you.
>
> **u/Loyalty4life187** (2 pts): How bout the guys on the book or the tube that wants to tell you how ya become a millionaire 🤣 and they ain’t even one..
>
> **u/_rbp_** (2 pts): I never really analysed picks, but my intuition is in most cases it might be the same as with "investment gurus" selling books - for most it goes, if they were really that good at predicting what will happen, they would simply be making money this way and not seeking a fee for sharing their wisdom.
>
> **u/Loyalty4life187** (2 pts): Sites because this year or maybe I’ve never noticed cause I never paid it no mind just used my own intuition is that what the experts tell people to pick I found that I’m not good at math but say for example SportsLine other night shot every pick wrong.  I mean right now it’s something to do ya know so I been doing basketball n football
>
> **u/Loyalty4life187** (2 pts): Yea I’m lost wish I knew what the heck was talking bout, I do parlays a lot n be off by like 1 game n what not.
>
> **u/_rbp_** (2 pts): Thank you! I hope for some feedback. The concept makes sense to me and works on my devices, and I hope to confirm it does for others too.
>
> **u/Loyalty4life187** (1 pts): I clicked on article what part/ NeverMind I got it
>

---

### [MLB Simulation Results Request for Benchmarks](https://reddit.com/r/algobetting/comments/1k6vwew/mlb_simulation_results_request_for_benchmarks/)
**Author**: u/AmateurPhotoGuy415 | **Score**: 2 | **Comments**: 8 | **Date**: 2025-04-24

Hey all, I've been working on an MLB model which relies on at-bat level simulation. Part of this model requires predicting pitching changes. I'm doing this in two stages: predict whether or not there is a substitution and then conditional on there being a substitution, predict from the available bench pitchers which will be the substitute.

  
I assume that most people would do something similar for an MLB simulation model. If you are currently doing this, I'd very much like to discuss with you performance on the conditional substitute model. I'm finding my performance to be lackluster but would also love to get some benchmarks to validate.

---

### [Anyone know the status of MySportsFeeds.com?](https://reddit.com/r/algobetting/comments/105q4et/anyone_know_the_status_of_mysportsfeedscom/)
**Author**: u/postrema19 | **Score**: 2 | **Comments**: 4 | **Date**: 2023-01-07

Hi All.  Long time lurker/first time poster.  I have a background as software developer and am very interested in this space, but am finding it difficult locating a good source of historical data and/or feeds.

I  recently stumbled across what looked to be a promising API provider at [MySportsFeeds.com](https://MySportsFeeds.com), but have found them to be unresponsive.   The API and data modeling seem to be pretty mature and well organized, but I recently found that it is not returning data for NCAAM basketball, so I'm beginning to wonder if this site is now defunct.

Does anyone have any insight into the status of this provider?  If not, any recommendations in terms of other providers in this area would be well appreciated.  I am primarily interested in data for the "big four" of the US (NFL, MLB, NBA and NHL) as well as college basketball data.

Any help or direction is greatly appreciated!

---

### [MLB Predict Relief Pitchers](https://reddit.com/r/algobetting/comments/1eadw7c/mlb_predict_relief_pitchers/)
**Author**: u/pipicks | **Score**: 2 | **Comments**: 5 | **Date**: 2024-07-23

I've created an MLB model which is currently seeing success in betting first 5 innings totals/spreads (relatively low sample size, but have been getting good clv so far). I want to extend this model to full games. The model is heavily reliant on the individual players in a lineup, so, currently the rotowire projected starting lineups are being used. 

Now I have ideas on how to model when the pitcher swap will happen, but I'm looking for suggestions on predicting the relief pitcher(s) that come on. My current thoughts are to look at past starts for the starting pitcher and obtaining a categorical distribution of possible (active) relief pitchers. I'm not a huge baseball fan so I don't know how naive this is. I appreciate any input.

---

## Closing Line Value & Market Efficiency

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [From Simple Models to Market Analysis: Is It Even Worth It?](https://reddit.com/r/algobetting/comments/1i7c0ma/from_simple_models_to_market_analysis_is_it_even/)
**Author**: u/National-Yogurt7021 | **Score**: 4 | **Comments**: 5 | **Date**: 2025-01-22

Some time ago, I started collecting historical data from football leagues and built a simple Python script. The script searches for teams in future matches based on specific criteria and finds teams with similar characteristics in the historical data. From a larger sample of the identified matches, it derives win probabilities and odds. I initially tested it with just one criterion, namely the average points per game. In the backtest, this resulted in a -12% yield, which didn’t surprise me, as it was extremely rudimentary. In that sense, it was amusingly a good contrarian indicator, so I tested a betting strategy based purely on randomness in the backtest. Even that performed better with a yield of -8%, lol.

I then planned to implement additional metrics to refine the model but decided instead to test the model provided by the site [xgscore.io](http://xgscore.io) by creating a Blogabet account. The reason was that I thought the approach used by the site seemed very sophisticated, and I probably wouldn’t be able to do better. On Blogabet, after 416 bets using their odds, I am currently at a yield of -7%. The sample size isn’t that large yet, but I find it hard to believe that it will improve significantly over time. The average odds are 2.318 (43%), with a win rate of 42%.

As of now, this would imply that the market odds (all bets placed on Pinnacle) pretty much reflect the actual win probabilities. This raises the question of whether it’s even worth pursuing such a project further, given how efficient the market seems to be. Respect to everyone who has managed to build a profitable model in these markets.

---

### [How sharp really is FanDuel on NBA props?](https://reddit.com/r/algobetting/comments/1keycjh/how_sharp_really_is_fanduel_on_nba_props/)
**Author**: u/jcmmania | **Score**: 3 | **Comments**: 4 | **Date**: 2025-05-05

I have heard through the grapevine multiple times that FanDuel is sharp on NBA player props. For this reason, as a top-down bettor I’ve been avoiding betting NBA player props into Fanduel, even when they diverge significantly from the rest of the market including actually sharp books like Pinnacle. Am I overrating Fanduel in this regard? Also, how does time from tip-off play into this (i.e. does Pinnacle’s edge over Fanduel increase as they take more sharp action on a given game)?

---

### [What sample size is significant?](https://reddit.com/r/algobetting/comments/18oltok/what_sample_size_is_significant/)
**Author**: u/verrts_ | **Score**: 3 | **Comments**: 9 | **Date**: 2023-12-22

I was doing backtests on +600 games. Although there is no look-ahead bias in my backtest, the results look a bit too good to be true:

* Sharpe ratio: 3.12
* Win rate: 46.5%
* Average ROI per won bet: 152% (edit for clarification: On average for every $1 won bet I get $2.52 in total. $1.52 is the profit).
* Risking 5% of the account balance per bet (initial balance: $1000) would yield at the end $55,000
* Biggest losing streak: 7
* Biggest drawdown: 36%

What do you think? Is it realistic? Is my sample size good enough to rely on this backtest?

---

### [Technical analysis on sports](https://reddit.com/r/algobetting/comments/1k0euwc/technical_analysis_on_sports/)
**Author**: u/Zestyclose-Gur-655 | **Score**: 2 | **Comments**: 0 | **Date**: 2025-04-16

On the stock market technical analysis of charts is very popular. 

Usually bookmakers don't offer any charts at all. (But they don't even want people to win, they barely show you profit and loss because they rather hide people are losing.)  
Some betting exchanges have charts, betinasia also does. 

Does it make sense to use any charts for betting and why not? 

Maybe i'm crazy but i found if i analyse a game, sometimes it's quite obvious where the money is coming in on. Because bookies just keep moving the price on one side. You can basically see it on the chart where people have been betting on. It kind of tells the story of that particular market.

In theory if you have a chart where the odds are constantly dropping, you first back at a good price then later lay it. This creates some value. Or vice versa with odds that are becoming bigger, so less of a % chance. First lay it then back it. 

The problem is maybe events that are going one side don't have to keep going that side. I think it does slightly more often then not but this is just an assumption that i make, i don't have hard data on if steamers more often then not keep steaming. 

I'm just trying to think like a bookie right now, essentially they just back and lay bets with a spread in between. This is similar to market makers, actually it is a form of market making. The real value then to me seems to anticipate where odds are going to, more so then where they are now. This is also true for gamblers, and even gamblers are just trying to beat closing line value, get a better value themselves. This indicates a profitable strategy. So if odds move in your advantage more often then not, this is part of the goal to me it seems. 

Say you was a bookmaker, in essence the best thing for them is have some markets that just go sideways forever with a big spread. They can constantly buy and sell, buy and sell and make a profit. Often you do see that odds move a certain direction. For bookmakers this is somewhat of a loss because their odds where first not correct. This is also why you can only bet little when an event is days away and big when it nears to start. The price has to shape to where it should be. Once everyone made their bets they know pretty good where it should about be priced. 

Maybe i spend too much time on the stock market but i do see also just trends, mean reversions, support and resistance in betting markets. In fact i think betting markets are even way more logical then financial markets. There might also be manipulation by single actors but for a bookie it's not good if odds are much different then where the real odds should be. Mispriced events makes it possible to value bet, since only the outcomes in reality influences the outcome of a bet. On financial markets it's mostly just price alone that has any meaning, fundamentals to a lesser extent. Option contracts are based on the price of the underlying not on the outcome of events. So there is much more what George Soros would call: "reflexivity" possible. Even the market participants itself can influence reality.

---

### [Live expected value betting?](https://reddit.com/r/algobetting/comments/111jg9a/live_expected_value_betting/)
**Author**: u/Quirky-Discount6828 | **Score**: 2 | **Comments**: 6 | **Date**: 2023-02-13

Assuming that you can you get to the line and place your bet before the odds change, are there any other pitfalls for live expected value betting? In fact, wouldn’t this increase your chances considering it would allow books to change odds from their closing line to a more accurate interpretation of how the game is actually being played out?

---

### [Closing lines from yesterday??](https://reddit.com/r/algobetting/comments/1fpzudx/closing_lines_from_yesterday/)
**Author**: u/Old-Pie-9913 | **Score**: 2 | **Comments**: 3 | **Date**: 2024-09-26

Yo! Does anyone know where you can see yesterday's closing lines across sharp books? Pinny, Cris, Circa, etc.? I'm able to find main markets but am looking for props. So far no luck...anyone know where I can find historical prop lines? THANKS!

---

### [MLB Predict Relief Pitchers](https://reddit.com/r/algobetting/comments/1eadw7c/mlb_predict_relief_pitchers/)
**Author**: u/pipicks | **Score**: 2 | **Comments**: 5 | **Date**: 2024-07-23

I've created an MLB model which is currently seeing success in betting first 5 innings totals/spreads (relatively low sample size, but have been getting good clv so far). I want to extend this model to full games. The model is heavily reliant on the individual players in a lineup, so, currently the rotowire projected starting lineups are being used. 

Now I have ideas on how to model when the pitcher swap will happen, but I'm looking for suggestions on predicting the relief pitcher(s) that come on. My current thoughts are to look at past starts for the starting pitcher and obtaining a categorical distribution of possible (active) relief pitchers. I'm not a huge baseball fan so I don't know how naive this is. I appreciate any input.

---

## Bankroll Management & Kelly Criterion

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [How do you deal with non-stationarity, infinite variance and distributional assumptions in sports data for betting models?](https://reddit.com/r/algobetting/comments/1jz4868/how_do_you_deal_with_nonstationarity_infinite/)
**Author**: u/Firm-Address-9534 | **Score**: 7 | **Comments**: 6 | **Date**: 2025-04-14

Hey all,

Layman explanation of non-stationarity:

Imagine you're tracking your team's performance week after week — maybe they're scoring more lately, or the odds for their win are shrinking. If the average numbers keep changing over time, that's non-stationary. It's like trying to aim at a moving target — your betting model can’t "lock in" a consistent pattern. Take this explanation with a grain of salt since it’s more complex than this simplification.

So historical data usually doesn’t reflect the current reality anymore. That’s why non-stationary data messes with prediction models — you think you’ve spotted a trend, but the trend already changed.  
  
Layman explanation undefined mean:

Normally, if you track enough results, you expect to find an average — like the typical number of goals in a match. But sometimes, there are so many extreme results (crazy high odds, or freak scores), that the average never settles. The more you track, the bigger it gets.

In simplified math terms:

This happens when the mean (average) doesn’t converge as sample size increases.

  
Layman explanation infinite variance:

Variance tells you how spread out the data is — like how far scores, corners, assists or odds swing from the average. If variance is infinite, it means you could see huge outliers often enough that you can't trust the spread at all.

In sports betting:

You might find odds or scorelines that are so extreme (say, a 200:1 correct score that hits more often than expected) that it wrecks any notion of what’s “normal.”  
Even if the average looks okay, you might suddenly hit a freak result that breaks your bankroll or model.

 

Layman explanation of distributional assumptions:

When you build a model, you often assume the data follows a specific “shape” — like a bell curve or a Poisson distribution. That shape is called a distribution.

Think of it like expecting:

Most football games to end 1–0, 2–1, 0–0, and only rarely 7–2

Or assuming odds behave in a way that fits a clean pattern, like normal distribution (the classic bell curve)

So, when we say, “distributional assumptions,” we're really saying:  
  
“I don’t know exactly what’ll happen, but I expect the numbers to behave kind of like this shape”  
  
Why Bad Assumptions Are Dangerous

 You underestimate risk:

Your model thinks rare results are “once in a decade” — but they happen every season.

Confidence intervals lie:

You think you have a 95% chance of winning a bet — but it's really 70%.

You miscalculated value:

You bet on “fair odds” based on the wrong distribution and lose long-term.  
  
Goals don’t follow Poisson or negative binomial as neatly as textbooks say  
  
Odds don’t reflect “pure probability” — they include public bias, team reputation, and market manipulation.  
  
Rare scorelines (like 5–4) aren’t that rare, but most models treat them like they are.  
  
  
I was thinking about implementing causal discovery and causal inference to better assess the problems that we face in the data.  
  
Any takes on this?

**Top Comments:**

> **u/Open_Future8712** (1 pts): Non-stationarity is tricky. I usually segment the data into smaller, more stable periods. For infinite variance, I use robust statistical methods like bootstrapping. Distributional assumptions? I prefer non-parametric methods. I’ve been using RobôTip for a while. It helps with soccer stats, making the betting process more data-driven and less guesswork.
>
> **u/Firm-Address-9534** (1 pts): 1- if the odds are  low enough you for sure can have 95% win rate.
0.25 of kelly criterion. Not 25% of your account, different things even if they converge to a close number in this example.
2- correct scores is liquid enough, offered by exchanges and sportsbook.
>
> **u/Badslinkie** (1 pts): Again, you're overestimating the similarities. For 1) You almost can't even place bets on odds long enough to give you a 95% win rate. I can't even think of a bet where they would take your action regularly at those odds, maybe betting 1 seeds ML every year in the NCAA tournament? If you're risking 25% of your BR on anything in sports betting you're going to get washed out. 2) You don't get to bet on whatever thing you want in this game, an operator has to offer it and they don't take a lot of money on the non main-stream bets. You're just never going to get down a significant amount of money on anything other than spreads and totals in this world.
>
> **u/Firm-Address-9534** (1 pts): Thanks for the comment.

It also depends on what you are betting, lets say you always bet on 3 or 4 most common correct scores. and you have 95% win-rate with it .in a bad streak where the results are skewed compared to what you previous thought was the mean.   
 Using kelly criterion at 0.25 you would loose 80% of the initial balance in 6 wrong bets.  


But i get your point of the losses being capped.
>
> **u/Badslinkie** (1 pts): You’re overthinking the relationship between finance and sports. 

In finance if you short GameStop and Reddit happens you lose infinity. In sports if two teams go to 16 overtime’s and score 6 sigma points and you’re on the under you just lose a bet.  In theory a 0 goal game happens with a similar frequency and these losses should wash. There’s just no world where a black swan event is wiping out 50% of your bank roll unless you’re risking that amount.
>
> **u/Firm-Address-9534** (1 pts): Im a quant and tbh most of the models in quantitative trading and risk are full of assumptions that are not met.
>
> **u/__sharpsresearch__** (1 pts): I like this question a lot. Iv spent a lot of time thinking about it and trying things. Iv taken a lot of my approaches from how people like Jane st look at markets (volatility as you mentioned but other time series variables, like differentials, Hurst, etc.) also a good parallel is weather forecasting.

Basically in the end imo, this is time series forecasting. And you can get a lot of what people are doing in finance and weather as they have done it for years and have spent a lot of money in the areas.
>

---

### [Universal Kelly Calculator](https://reddit.com/r/algobetting/comments/1k0pgyt/universal_kelly_calculator/)
**Author**: u/vegapit | **Score**: 5 | **Comments**: 8 | **Date**: 2025-04-16

Hi there,

I have worked on an algorithm to find the optimal Kelly fractions for the most general use case i.e. multiple simultaneous independent bets each with multiple exclusive outcomes. Its inner workings are briefly described in this short article on my [blog](https://vegapit.com/article/universal-kelly-calculator). You can also directly give it a try [here](https://vegapit.com/kellycalculator).

Have a great day

**Top Comments:**

> **u/vegapit** (1 pts): To be clear, my claim is just that it is a good compromise between accuracy and speed of convergence for this very SPECIFIC case. Not much else, really.

I have exported the Rust algorithm to a Python module, so benchmarking should be easy to set up.
>
> **u/statsds_throwaway** (1 pts): i thought clarabel supported exponential cone programs
>
> **u/vegapit** (1 pts): Yes, speed of convergence. I am not familiar with Clarabel, but reading the doc, I don't think I could use it for 2 reasons:

1. My objective function is not quadratic. I can apply a taylor expansion to make it approximately so, but this would be wrong for certain bet parameter values.
2. It does not handle bounds on the decision variables at the local or global level.
>
> **u/statsds_throwaway** (1 pts): fair play, your last paragraph clears up things nicely

regarding your point about general tools, what do you mean by performance? as in runtime? i would be surprised to see a significant enough gap between your implementation and a solver like clarabel
>
> **u/vegapit** (1 pts): There are open source solvers for convex problems available in Rust. I plan to benchmark the current solution with one.

Otherwise, open source is indeed great but from experience, using very general tools to solve specific problems is often not optimal for performance.

There is no paywall at the moment. Just me limiting the computing load on my server by reducing the input data size =:D
>
> **u/statsds_throwaway** (1 pts): i see, that's an interesting rule. i've read your write-up before on using gradient ascent so would be interested to see how it holds up against more direct convex opt algorithms such as interior point methods
>
> **u/vegapit** (1 pts): Thanks, my algo is in Rust, and my general rule is to avoid third-party dependencies if possible. It could be useful to benchmark it against, though.
>
> **u/statsds_throwaway** (1 pts): you can do this pretty easily with CVXPY
>

---

### [Where does Star Lizard and other large scale betting co’s place its bets?](https://reddit.com/r/algobetting/comments/1kf7vtu/where_does_star_lizard_and_other_large_scale/)
**Author**: u/dtl85 | **Score**: 3 | **Comments**: 3 | **Date**: 2025-05-05

Question as above - most of us are aware of Tony Bloom/Star Lizard/and some of the other large betting co’s, and my question is - where would companies like this place its bets? 

Can’t imagine it’s easy to just drop some potentially huge stakes into Betfair Exchange? Also, it’s a company too - I thought Exchanges only cater for individuals?

---

### [Model Evaluation](https://reddit.com/r/algobetting/comments/1fzzp9e/model_evaluation/)
**Author**: u/usmanirale | **Score**: 1 | **Comments**: 16 | **Date**: 2024-10-09

I am backtesting a model, and after backtesting for seven seasons, I got the following result: I start each season with a 1000-dollar bankroll, using the Kelly criterion and a max stake of 2% of the bankroll. I want to know if this outcome is inline with a winning model.



1. Win Rate:

2024: 60.32%

2023: 75.36%

2022: 42.67%

2021: 37.50%

2019: 50.56%

2018: 55.32%

2017: 52.63%



Average win rate: 53.48%



2. ROI (Return on Investment):

2024: 51.77%

2023: 117.78%

2022: -21.42%

2021: 0.05%

2019: 70.33%

2018: 26.64%

2017: 26.32%



Average ROI: 38.78%



3. Average Value Percentage:

2024: 28.72%

2023: 25.80%

2022: 34.19%

2021: 45.74%

2019: 29.48%

2018: 40.10%

2017: 29.11%



Average value percentage: 33.31%



4. Log Loss (Predictive vs Historical):

2024: 0.4643 vs 0.4765

2023: 0.5018 vs 0.5488

2022: 0.5197 vs 0.4999

2021: 0.4829 vs 0.4896

2019: 0.6484 vs 0.6531

2018: 0.5355 vs 0.5650

2017: 0.5827 vs 0.5828



Average Predictive Log Loss: 0.5336

Average Historical Log Loss: 0.5451



5. Profit/Loss:

2024: +$517.68

2023: +$1,177.78

2022: -$214.17

2021: +$0.54

2019: +$703.31

2018: +$266.43

2017: +$263.24



Total profit over 7 seasons years: $2,714.81

---

### [Fractional Kelly Criterion approaches?](https://reddit.com/r/algobetting/comments/m7lknn/fractional_kelly_criterion_approaches/)
**Author**: u/simiansays | **Score**: 1 | **Comments**: 18 | **Date**: 2021-03-18

Hi, do folks here use the Kelly Criterion? Just wondering what approaches you use for translating a Kelly number into an actual allocation.

At the moment, I'm just doing a 15% fractional Kelly but wondering if anyone has spent much time tuning Kelly-based allocations. I vacillate between thinking 15% is too agressive or too conservative. Most of my positions end up being around 1-5% of bankroll. I picked this number to minimize drawdown risk but am toying with the idea of increasing it slowly as the bankroll grows and I get a better feel for the model.

I'm also moderating my model's perceived edge to reduce the instances of huge Kelly recommendations - at the moment, I'm just chopping all perceived edge in half which feels about right.

The main drawback I see right now is that it feels like I'm under-allocating the rarer longshots where the perceived edge is large, and based on my results the real edge was also large but the Kelly recommendation for those plays using this system was very small (usually \~1% of bankroll). Curious if anyone has encountered the same thing.

This article was the most mathy one that I could still (mostly) absorb on the topic: [https://caia.org/sites/default/files/AIAR\_Q3\_2016\_05\_KellyCapital.pdf](https://caia.org/sites/default/files/AIAR_Q3_2016_05_KellyCapital.pdf)

---

## Machine Learning Approaches

### [Tennis Analysis #2: Upset Victories](https://reddit.com/r/algobetting/comments/11v0289/tennis_analysis_2_upset_victories/)
**Author**: u/quant_boy123 | **Score**: 12 | **Comments**: 1 | **Date**: 2023-03-18

Hello everyone,

It has been a while since I started what was supposed to be a series focused on tennis analysis from a sports betting perspective. In my first [post](https://www.reddit.com/r/algobetting/comments/ujmpv7/tennis_analysis/), I gave some insights into my motivation and an overview of my data. I also discussed two topics, Implied vs. Realized Probability in tennis betting and O/U Game Lines (theory vs. reality). Moreover, I conducted some backtests based on very simple strategies.

&amp;#x200B;

* Background

My goal for the future is to post more frequently and thereby give you all some trading ideas and valuable insights into tennis analytics. I will typically start with some theory, derived statistics and eventually show some real world betting strategies based on the findings. Whether they would be profitable or not is irrelevant, as both can provide important insights. A bad bet not taken is probably equally valuable as a good bet.

&amp;#x200B;

* Data

For this article, I am only looking at men’s results in official matches for which I have a minimum threshold of data required for the research. My dataset has been growing rapidly recently, since all tournaments have started to resume from the COVID break. Overall, 2022 saw a similar amount of matches as 2016-2019 did (roughly 30000 with clean data) and 2023 is on track to match that. It is important to note that both the quality and quantity of data increased steadily, with more than 60% of the high quality data coming from years &gt;2015.

&amp;#x200B;

* Surprising Outcomes

Today I want to look at upset victories/wins. My definition of an upset is based on bookmaker odds, not on ranking or any other statistics. Bookmaker odds reflect the best guess for the outcome of a match in an efficient market, since they not only take into account the ranking of the two players or their form, but also factors such as the surface, head to head outcomes between the two players and more. Therefore, an upset win can be defined as a win of a player with odds greater than a threshold, let’s say 3 (= Implied Probability roughly 30%, adjusted for vig). 

Firstly, I filter the data to only include players with at least 20 completed matches. Secondly, I exclude players with less than 5 upset wins. Then I start with looking at upset wins with a threshold odd of 3, so every win of a player with odds &gt;3 qualifies as upset win. Since surprises tend to scale with matches played, I rank the outcome by the percentage of upset wins to total matches the player entered as an underdog with odds &gt;3.

Most players making the top 50 of that statistics are ‘newer’ players. This has to do with the fact that most of the high quality data is from recent years, as explained in the Data section. Thus, upset wins from players like Novak Djokovic or Roger Federer are very unlikely, since the data is mainly from a time when they were entering almost every match as a favorite and if they were an underdog, it was typically not with odds &gt;3. 

It is straightforward to see that upset victories typically come at the early stages of the career of a tennis player. That is, when the bookmakers do not have enough information about a players skill. Once they have made some surprising wins, bookmakers lower the odds of the player in subsequent matches to reflect the updated information about their skill level more accurately. Their next wins may therefore not qualify as upset wins anymore, since the odds can be significantly lower than the threshold. This becomes obvious when looking at the odds history of a player like Carlos Alcaraz.

[Graph 1: Carlos Alcaraz ranking vs rolling median odds with a window length of 25 matches.](https://preview.redd.it/k4ugps6iyjoa1.png?width=432&amp;format=png&amp;auto=webp&amp;v=enabled&amp;s=ad92a53e46c91a5f801f8693b075dde24a266b77)

In this graph, the median odds with a rolling window of 25 matches are used. This has the advantage that the curve is smooth and a trend can be easily spotted. Median odds are used instead of average, since the average can plateau on a high level due to one match against a top opponent, for instance Nadal in the French Opens, with very high odds.

In his early days in 2019, when he was first competing in challengers and mainly futures, he often was the underdog. After quick initial success, however, he mainly entered futures tournament matches as the favorite. The same happened in challenger matches in 2020, when he dominated almost every tournament he entered. In 2021, he shifted focus to main tour events, where he often was the underdog. This is where his median odds increase again. In 2022 he had some great victories in the main tour, thus his odds decreased and are now among the lowest of all players, making him the favorite in almost any matchup.

In the following graph, we follow a simple strategy: bet 1 unit on Alcaraz whenever the odds are &gt;3. Obviously, this is with a good portion of hindsight and not a f

[... truncated, see original post ...]

**Top Comments:**

> **u/zahaha** (1 pts): As someone who just got into modeling Woman's Tennis, these are amazing. Please keep it up!

You ever look at live betting trends? Im sure its very hard to get the historical live lines but im curious if there are any situations when "if the pre match odds are &gt;-200 and the live line gets to +300, always take it", or stuff like that.
>

---

### [Soccer Value Betting Team](https://reddit.com/r/algobetting/comments/120mki5/soccer_value_betting_team/)
**Author**: u/AssignmentHelpful | **Score**: 8 | **Comments**: 8 | **Date**: 2023-03-24

Hey pals, I’m looking to build a small team (3-5 people) to develop a system to price the following soccer markets: moneyline, over/unders and Asian handicaps. 

I recognize the difficulty in pricing soccer given the popularity of the sport, the high cost of data and the competition from big betting syndicates, but I believe there are pricing inefficiencies that we can exploit using feature engineering on event data. The development of the infrastructure will most likely take between 5-10 months with the right people. I have already tackled some of the scrapping and data wrangling required, but I’m still far from having a streamlined system.

The project will entail:
- Scrapping and cleaning event data (started)
- Scrapping and cleaning odds data (started)
- xG, xThreat model implementations (started)
- Feature engineering 
- Developing machine learning modes
- Testing accuracy of the models
- Deploying everything to servers/cloud

This should be a fairly big project, so I don’t expect many of you to be interested. 
The worst case scenario is that we don’t find any edge, if that’s the case we would still have the infrastructure to do any other projects regarding soccer. 

Let me know if you are interested or if you are just curious about the project and it intricacies.

PD: I’m coding in python and storing data in SQL

**Top Comments:**

> **u/TheBigLT77** (1 pts): New to algo but ten years betting on soccer and played at a high level. Happy to help
>
> **u/yungreseller** (1 pts): I’d recommend a different sport, if you print the premium free pinnacle odds against the odds implied by results, you usually find that if there are mispricings they are usually covered by the bookies premium. I mean think about it, in this market alpha can only exist for you, if you are the only one knowing it.
>
> **u/AssignmentHelpful** (1 pts): The idea would be to develop models that beat the closing line on sharp bookmakers (pinnacle and betcris), so that you can consistently bet sizeable amounts on these sites without the danger of getting restricted or banned. Way easier said than done, but I’m certain that it’s achievable on some markets.
>
> **u/boardsteak** (1 pts): How do you expect to capitalize on your results?
>

---

### [My attempt at a model to bet on NFL games](https://reddit.com/r/algobetting/comments/ggaz71/my_attempt_at_a_model_to_bet_on_nfl_games/)
**Author**: u/HamirTime | **Score**: 8 | **Comments**: 14 | **Date**: 2020-05-09

Hey guys, been lurking since this subreddit got created and knew I would be contributing to it once I got my model to an "acceptable" state to hopefully get further insight.

Gonna try to keep this as short as possible because alot of explaining happens in the Jupyter notebook, but here goes.

So basically I took a data mining course this last semester and the final project was to apply the concepts we learned in class to a real world scenario. While the NFL was in full swing, I was a frequent sports better and would really enjoy betting and watching the games. Data and modeling still seemed like such a complex topic to me, but I knew that eventually I would the subject either in class or on my own. After learning the data mining world, this in-class project was a perfect way to test what I had learned as well as try and use my skills to make some money.

SO with all that out of the way, the summation of the actual data and models is that I took game data from Kaggle (mainly used to pull the scores) and added full team rosters for both away and home teams (rosters scraped from another site). My thought was that since each team is composed of 52 players, that at the end of the day their performances (with the leadership of the head coach) is what determined the outcomes of the game. So to summarize, each of my records contained the home and away teams, current W-L records, and most relevant positions for both teams. I also decided to filter the data to only be within this millennia.

With this data I tried to use regression models to predict the score of the games. This score would then be compared with the vegas spread for that game so that the model could predict whether it should bet on the home team or the away team to cover the spread. This might not be a good practice, but I just decided to use every game from the 2000-2018 season to predict 2019 games as my model testing phase. I used the SVM Regressor algorithm (primarily because it was the only one that supported unbalanced data, which is obviously important since the more recent games should play a bigger factor) and an Artificial Neural Network because it's pretty easy to grasp and honestly doesn't require much thinking or work from me. Kinda also used it in case I was configuring the SVM wrong.

In summary, my results were slightly worse than I was expecting.  Both my models average out to about 52% accuracy and a mean squared error of around 195 when compared to the actual point values. Hence the main reason I am posting here: to get some help from more experienced data scientists.

I've decided to include my work here, both for more experienced people to critique and maybe for some less experienced people to learn. This project was, again, done as a school project so please excuse some of my markdown comments as they had to follow a format for the class. This is also done in Python primarily using scikit learn for all data modeling and pandas for pre-processing. I used VS Code as my IDE with the Microsoft Python plugin to view and edit Jupyter Notebooks.

I want to keep developing this in the future, at this point not even to make money but just because I think it's a cool concept. The thought of math being able to better predict as complex a game as football more accurately than almost anyone is crazy. Other than this model, I recently also purchased a Raspberry Pi (also being used for other side projects) to eventually automatically pull new game data for the model to predict.

Like I said above please feel free to critique, this was basically my first major python project and I had no experience with any of these libraries. Also don't usually post on Reddit so if my formatting sucks call me out on that too.

Thanks guys, hope this is a helpful post to keep the subreddit going.

Jupyter Notebook: http://www.filedropper.com/finalproject_2 (not sure how long the site will host the file TBH)

**Top Comments:**

> **u/15woodsjo** (4 pts): To piggy back off this answer, I would also throw in a suggestion of using a neural network and turning this into a binary classification problem.

In practicality this is a logistic regression model that you have more control over, and can potentially get a little bit better of a model out of the algorithm.

&amp;#x200B;

The reason I would suggest anything binary classification for this type of problem is you would want to be able to measure the % likelihood of one team vs. another covering the spread whilst the line moves. In essence, you can get more information by knowing that team A has a 60% likelihood of covering a (-9) line and team B has a 40% chance PLUS team A has a 55% likelihood of covering a (-10) line and team B has a 55% chance. Basically you want to be able to apply your model to a dynamic line to get what is hopefully a more accurate picture of a +EV game
>
> **u/KidMcC** (3 pts): Will respond more fully later, but one thing that jumps out at me is that you might want to explore using a GLM with Poisson distribution as opposed to something like SVMs for football scores. This allows you a better probability assignment to different outcomes. 

Basic googling should land you more stats-focused details on that.

As an aside, there are better ways to handle imbalanced data than using an SVM for assigning binary winner/loser status. SVMs rarely perform consistently better than some other such models, like Logistic Regression or Random Forest Classifiers. Looking into weighted logistic regression or sub-sampling to balance out data as opposed to picking a specific model family as a result.

&amp;#x200B;

Again, will respond more later, as it's an interesting problem. Also open to debate re: any of the above.
>
> **u/15woodsjo** (2 pts): That's fair, my background is in basketball where I suppose there is a larger sample size.
>
> **u/KidMcC** (2 pts): This is a very important distinction. "Binary classification" can be done at least two ways here.   
1) Linear model (of sorts) fit to predict the point difference (homeScore - awayScore). Again, GLM approach with Poisson Distribution is the most common choice for football for a reason, given how scoring is not linear with each point-accumulating event. The sign of the endogenous variable would then be indicating the "win" the same way a 1/0 would in your example. Here you can use size of the difference to indicate probability, to some degree.   
[https://www.sbo.net/strategy/football-prediction-model-poisson-distribution/](https://www.sbo.net/strategy/football-prediction-model-poisson-distribution/)

[https://www.pinnacle.com/en/betting-articles/Soccer/how-to-calculate-poisson-distribution/MD62MLXUMKMXZ6A8](https://www.pinnacle.com/en/betting-articles/Soccer/how-to-calculate-poisson-distribution/MD62MLXUMKMXZ6A8)

2) Ignore points and predict an actual binary variable indicating whether or not the home team won. What this modeling approach provides is a direct probability associated with each classification. This also requires a choice to be made of regularization, L1/L2 penalty if using Logistic Regression, etc.  


Predicting scores via regression, and then daisy-chaining that back into a spread comparison to then take advantage of error profiling, like you said, is quite indirect and will certainly introduce more bias and/or volatility than what it returns in accuracy.
>
> **u/KidMcC** (2 pts): If we are talking about predicting binary game outcome, then I'd be hesitant to go the route of neural network. By its very nature of scheduling and season construction, football doesn't offer a huge dataset of games to really draw from (compared to other sports). Especially if you aren't weighting games from the distant past fairly, one can find themselves with a high variance, over-parameterized model fit on too little an amount of data. All my opinion of course! 

I do think a thoughtful feature selection process fit to an XGB or RandomForest model might be more manageable given that gameplay data gets old fast. Exponential weighting can be your friend here, though, if you need to go way back, just make sure your offense-profiling is dynamic!
>
> **u/15woodsjo** (2 pts): You are implementing a binary decision based on your model but not using an algorithm that is trained using binary classification. Slight difference
>
> **u/HamirTime** (2 pts): Thanks for the insight, I will definitely look into GLMs and their applications. I'm more familiar with logistic regression, so I would probably err towards looking into that to better handle imbalanced data
>
> **u/HamirTime** (2 pts): I could be misunderstanding your suggestion, but I think I am currently already transforming this into a binary classification problem. After using regression to calculate the score, I compare it with the spread to calculate a 'class' variable (0 or 1). 0 meaning a bet should be placed on the away team and a 1 meaning a bet on the home team. I use these to also measure common metrics like accuracy, precision, and recall.

 The likelihood percentages was also something I wanted to implement by using the difference between the predicted score and the spread, but wanted to focus on improving the model before then
>
> **u/anxiousalpaca** (1 pts): You are right, i totally misread what is meant by daisy-chaining back (not an English native speaker)
>
> **u/KidMcC** (1 pts): The OP said nothing of features describing the relative defensive capability of either side of the ball. Without such features, I'd still say daisy-chaining yhat values for score back into a comparison is risky, as it leaves nothing in the model reflecting the fact that for one team's offense to have the opportunity to score, it generally requires that the other team does not have the same opportunity at the same time (save for pick-6s). Volatility would be unstable when you begin to use this approach with games where disparity between defensive capability on each side is substantial. At least, this is what I have found. Curious to hear more if this is still at odds with your experience.
>

---

### [Moving past the Basics (EPL)](https://reddit.com/r/algobetting/comments/psbvxy/moving_past_the_basics_epl/)
**Author**: u/ProdigyManlet | **Score**: 6 | **Comments**: 12 | **Date**: 2021-09-21

Hi everyone, I'm looking at creating an algorithm that predicts the outcome of EPL matches and provides the odds for value-seeking (seems the easiest place to start given the popularity and availability of data). The introductory approach seems to be modelling the expected goals scored by both teams using a Poisson distribution, which is a nice and intuitive model to start with (at least for someone with a bit of an applied stats background).

I'm now looking into more advanced classification methods that predict the outcome of a match between two teams. So far my classification model is getting 50% accuracy using only historical match result data (slightly transformed), so hopefully that's a good starting point. I've got some ideas for more features to add from reading a few papers and some intuition (e.g. manager data, weather, etc.), but was wondering what others found was effective or if they had any lessons learned in moving forward on the modelling side?

This might be too open ended, but some common themes and areas of interest I thought my be relevant to others are:

* How were people's experience with tmproving the basic models (e.g. Poisson) versus moving to classification models (e.g. traditional machine learning)?
* Aside from train/val/test data splits &amp; backtesting, what other techniques did people find effective for evaluating the accuracy or the reliability of their algorithm?
* Did anyone find any common misconceptions? (E.g. chasing down weather data only to find it's impact on model performance was limited).
* Any general types of data aside from match results/historical goal performance that were found useful?

**Top Comments:**

> **u/Davidweb1337** (3 pts): Im not experienced with running models or machine learning so i don't know what kind of data you're looking for. But from what I've heard in the industry, it's been very difficult to find live data feeds for League of legends, especially in China since the organisation running the tournaments over there are apparently not selling any live feeds to betting companies, often leading to latency issues and poor trading on the bookmaker's side. It's usually an esports trader manually adjusting odds while watching the stream haha. Or no live betting offered.

From what I could find, someone has already attempted to build a model here: (includes a link to a dataset, under downloads &amp; tools) https://www.quantumsportssolutions.com/blogs/league-of-legends/a-predictive-model-of-league-of-legends-game-outcomes
>
> **u/lequanghai** (2 pts): Where do you get data for esports? I mostly play and follow League of legends but cant find any complete dataset or source to perform analysis &amp; live betting.
>
> **u/Davidweb1337** (2 pts): E-sports is quite inefficient actually. It has only really started ramping up in the past few years but is still dwarfed by most traditional sports so bookmakers don't really invest as much into R&amp;D for it. You're very likely to find stale prices/lines here, but also very low betting limits.
>
> **u/bananarepubliccat** (2 pts): Yes,  most of the things you mention perform pretty poorly in reality.

Rolling window methods aren't that useful. You want to use season data with possibly priors from the previous season. Again, it is how information gets incorporated. With filter models, the update cycle is capturing all the right information...with rolling windows, you are getting some approximation of skill using unimportant information (against weak opponents, very old matches, etc.). You can weight more recent matches but it still won't beat ELO.

Btw, I didn't make this totally clear in my previous comment: the reason why these sports are hard to model is because the data is adversarial. The information comes from interactions between two teams, it is not only team skill but opponent skill that matters. This is particularly bad in football because you can have teams that win by doing things that would cause other teams to lose (this is less common in other invasion sports where there is usually a dominant strategy)...for example, if you have a model based on possession, teams that counter-attack will be rated poorly...and even then, that counter-attack strategy may only work against certain kinds of teams. And then you have a difference between offensive and defensive strategies: for example, Newcastle always used to outperform vs good teams because they were so defensively solid, but lost it whenever they had to attack the other team. It is very tricky. So an ELO model that has far less data will outperform because the ratings and difference of ratings capture the maximum amount of information.

If you are able to use some non-parametric grouping and then incorporate that into your rating then I think you would be able to produce a more traditional ML model that works (i.e. this team is a counterattack team against an attacking team so we expect X fast breaks, and they got X+5 so we increase their rating)...but even then, I still think the update cycle of filter models like ELO is very effe [...]
>
> **u/king-chungus** (2 pts): Don’t do deep learning, but I definitely think log regression, SVMs, etc… can be viable
>
> **u/ProdigyManlet** (2 pts): Thanks for the extremely detailed reply, this is absolutely awesome and is riddled with great info that answers a whole bunch of my questions (and some I hadn't even thought of yet).

By classification and traditional machine learning I'm referring to things like logistic regression, decision trees/random forest, support vector machines, etc. Basically traditional machine learning is non-deep learning methods. I definitely think Deep Learning would perform pretty poorly in most betting algos given the small data quantities.

In terms of data, I was using a rolling window (e.g. N games like you mentioned) that rolled across prior seasons to avoid the issue of say if N = 20, but we're at match 5 then there's only 4 data points. Obviously a lot changes between seasons which is not accounted for, but I was hoping to factor in information that captured these changes later on (i.e. manager changes/metrics and some form of player metrics). The Brier score looks good, and I like the idea of the ELO approach as it's much more manageable, simple and looks like it will be less reliant on across-season data; will look into all of these.

I had a feeling that the bigger markets will be more difficult. I will still try to get my basic model framework up and running using EPL, and then switch to some local leagues in my own country (looks like I can get the same data in basically the same format so should be an easy switch). I wanted to stick with a sport I have good domain knowledge in as I want to keep it interesting as a hobby while reviewing my classical statistics knowledge (I'm experienced in Deep Learning and Traditional ML, but it's been a while since I went back to the basics of distributions). However, I'll definitely take the suggestion onboard and look at some more obscure markets on the side. I was thinking of E-Sports but I would assume that might be quite efficient too.
>
> **u/TraptInaCommentFctry** (1 pts): &gt;you only update when you see something unexpected, the whole measure is weighted against peers

could you clarify what you mean by this?
>
> **u/bananarepubliccat** (1 pts): That isn't what I said.

I have used data that costs $100k+ annually, the features don't matter if you start from the wrong place (I explained this above, if you are seeing similar predictive power from ELO as ML then you have gone very wrong because ML, as most people are doing it, doesn't work...tbf, most people don't do ELO right either but that isn't a problem with the model). This varies by sport but the OP asked about soccer.

Using ELO as a feature is a basic error (and again, you are missing the point massively). ELO is just a filter, so you can use your ML model as an input to ELO: it is just a map from joint distribution of skill to prediction for a feature, so you can use ML as an input to ELO (I wouldn't advise building a mixture with ELO either, that is a very bad idea practically for soccer because of lineup changes).

How you do this is more complex but the key is that you are modelling a joint probability, that is where the power comes from. What OP will have tried is: X feature over N games or something similar, these models don't work (you can modify features, but it still won't get close). You can get them into a joint probability but, again, the problem is that they don't represent information correctly (again, this is obvious when you think carefully about what you are actually modelling...most people, inadvertently, end up with a single distribution for the average team...this works particularly poorly in soccer where there is no strategic equilibrium i.e. the meaning of features varies hugely based on the team).
>
> **u/MathMod3ler** (1 pts): Thanks for clarifying the original comment. Respectfully, I disagree that traditional ML is incapable of handling that amount of information. I think it comes down to having good features. Although, in practice I prefer using several ELO models as features in my ML models. So I definitely like the information ELO captures.
>
> **u/MathMod3ler** (1 pts): I disagree with a lot of this thread. Although, I think reasonable minds can disagree on this sort of stuff. I would say a couple things to take your modelling to the next level:

1)Stack uncorrelated models.
2) Use the betting market as a starting point for some of your models. The betting market is already a damn good model. Build on top of it, it already takes into account many of the basic features (probably including Poisson Distribution of goals). 
3) Come up with different targets. Ex: Win-Loss Binary and Difference in goals (they both tell you the betting outcome but the computer will look at them very differently).
4) Have way bigger test-validation sets than the normal rules of thumb. Finding patterns is easy...finding persistent patterns is hard.

My two cents, classification is fine. Just really do a lot of safe-guards and validation.
>

---

### [NFL Passing Attempts Model Advice](https://reddit.com/r/algobetting/comments/1k67adj/nfl_passing_attempts_model_advice/)
**Author**: u/toddinvesterguy12 | **Score**: 5 | **Comments**: 7 | **Date**: 2025-04-23

Hey everyone, I just tried for the first time to build a model that predicts a players pass attempts. I collected 3 years of data via scraping/APIs with columns formatted as 

Date of game,
Player,
Pass attempts in game,
Players team at time of game,
Home/Away,
Opponent team,
Player’s Coach,
Game start time,
Location of game,
Average temperature during 4 hours from start of game time,
Type of precipitation if any,
How many hours in four hour window precipitation occurred,
Pre game points total at fanduel and DraftKings,
Pre game total odds at fanduel and DraftKings,
Pre game spread for players team at fanduel and DraftKings,
Pre game spread odds for players team at fanduel and DraftKings,
Pregame pass attempts total at fanduel and DraftKings,
Pregame pass attempts odds at fanduel and DraftKings

I have minimal experience with coding (2 intro level courses in python and R), so I loaded this data into Claude and promoted it to create linear regression and random forest models with the data. I prompted it to train on half and test on the other half. Both achieved an r2 of around 0.4 so not good. 

At this point, I’m curious if I’m trying to predict a metric that is too volatile, if I need more data using the same features, if I need to add additional features, a combo, or if I’m missing something else I should learn about before proceeding. 

Appreciate any advice.

**Top Comments:**

> **u/cortezzzthekiller** (6 pts): Props are generally about predicting volume -- and passing attempts is ALL about volume. So you are missing a huge part of the puzzle here -- off/def plays per game
>
> **u/2kungfu4u** (2 pts): Huge agree here. I'd also argue in tandem with that you'd mostly likely want to include metrics like pass rate over expectation, pass rush splits on a given team and maybe even team record. It's one thing to include the spread indicating if they're a dog or not but how often they are a dog is valuable as well imo
>
> **u/Golladayholliday** (2 pts): I mean… What is the point of this model? To beat the books? To do some learning? 

You included the book odds, any good model is just going to violently latch on to that with the other things you have included(missing some major pieces). You very likely have built a devigger 😂. This is where the journey starts tho. Keep on pushing. 

I think the best piece of advice I can give you is what I wish someone had told me. ML/AI isn’t magic, it’s an extension of your expertise. You can huck a bunch of data at a model and you might get a okay baseline, but that is not what makes a model great. You need the domain knowledge and ML knowledge to know what is important and how to present (feature engineer) it, and if done right it will come to very similar conclusions as an expert would. 

The difference is it can do it in less than a second instead of an in depth time consuming expert review. That’s the magic.
>
> **u/Golladayholliday** (1 pts): It’s going to be tough only because you’re essentially feeding a much better model back into your model as an input that’s likely considering all the same things you are plus a lot more. 

The other thing to accept is most bets there is no +EV side. I have a very solid baseball model, and if I had to estimate about 80% of the time I get some number that’s between the spread(both sides lose money long term), 10% it’s very light value (picking up a quarter or 2 of EV on my $50 bet) and 10% it’s decent.
>
> **u/toddinvesterguy12** (1 pts): Essentially I want to connect the predictions it makes to +EV sides on passing attempt bets. For now I just need to learn more about machine learning and how best to present data to these models and I really appreciate your insights
>
> **u/toddinvesterguy12** (1 pts): Appreciate it that’s a great idea
>

---

### [How useful is something like this](https://reddit.com/r/algobetting/comments/1k662a4/how_useful_is_something_like_this/)
**Author**: u/Forsaken-Hearing3540 | **Score**: 4 | **Comments**: 17 | **Date**: 2025-04-23

www.playerprobabilities.com

I’ve been working on a machine learning model to predict NBA player props — specifically points, assists, and rebounds. Originally, I used linear regression (with Lasso for feature selection) and rolling averages to predict raw values. That alone gave me around 57  - 70% accuracy on some given days, this is for 68+ players on game days.

Now I’ve taken it a step further:
I treat the regression prediction as a mean,
Calculate a confidence interval using a z-score (95% confidence),
Run Monte Carlo simulations to estimate the distribution of outcomes,
Then compute the probability a player hits the over/under line.

Also a second reason why I am here ,can you guys share any tips on how you guys account for lineup changes and how it affects what a player is going to score. I have really been struggling with that aspect of things.l

---

### [Exploring In-Game Predictions with Odds Data – Would like to Collaborate](https://reddit.com/r/algobetting/comments/1hni8vu/exploring_ingame_predictions_with_odds_data_would/)
**Author**: u/97wschultz | **Score**: 3 | **Comments**: 2 | **Date**: 2024-12-27

Hi everyone,

I’ve been working on a project where I collect odds data at 40-second intervals for EPL and Championship matches, with the goal of exploring whether in-game predictions can be made using this data alone.

I’ve had some promising results so far with models like XGBoost and logistic regression, but there’s plenty of room to build on this. My main focus is on expanding the models and gaining a deeper understanding of the possibilities.

This is more about learning and experimentation than making money. If anyone is interested in getting involved or exchanging ideas, I’d love to collaborate and see where this could lead!

---

### [Feedback wanted for a ML prediction model](https://reddit.com/r/algobetting/comments/1jrd44c/feedback_wanted_for_a_ml_prediction_model/)
**Author**: u/Jp46810557 | **Score**: 1 | **Comments**: 7 | **Date**: 2025-04-04

A few of us have been working on a machine learning model to predict NBA game outcomes (Moneyline, Spread, O/U). We're in the early stages and would love to get some feedback from the community on its potential and areas for improvement.

Our model considers factors like team performance, recent game history, and some contextual elements. We're particularly interested in hearing what you think are the most important indicators for predicting NBA games accurately.

If anyone is interested in seeing some of the model's daily predictions and providing feedback, feel free to DM me and I can share more info. We're really focused on learning and making this a useful tool.

---

## Tennis

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [Tennis Analysis #2: Upset Victories](https://reddit.com/r/algobetting/comments/11v0289/tennis_analysis_2_upset_victories/)
**Author**: u/quant_boy123 | **Score**: 12 | **Comments**: 1 | **Date**: 2023-03-18

Hello everyone,

It has been a while since I started what was supposed to be a series focused on tennis analysis from a sports betting perspective. In my first [post](https://www.reddit.com/r/algobetting/comments/ujmpv7/tennis_analysis/), I gave some insights into my motivation and an overview of my data. I also discussed two topics, Implied vs. Realized Probability in tennis betting and O/U Game Lines (theory vs. reality). Moreover, I conducted some backtests based on very simple strategies.

&amp;#x200B;

* Background

My goal for the future is to post more frequently and thereby give you all some trading ideas and valuable insights into tennis analytics. I will typically start with some theory, derived statistics and eventually show some real world betting strategies based on the findings. Whether they would be profitable or not is irrelevant, as both can provide important insights. A bad bet not taken is probably equally valuable as a good bet.

&amp;#x200B;

* Data

For this article, I am only looking at men’s results in official matches for which I have a minimum threshold of data required for the research. My dataset has been growing rapidly recently, since all tournaments have started to resume from the COVID break. Overall, 2022 saw a similar amount of matches as 2016-2019 did (roughly 30000 with clean data) and 2023 is on track to match that. It is important to note that both the quality and quantity of data increased steadily, with more than 60% of the high quality data coming from years &gt;2015.

&amp;#x200B;

* Surprising Outcomes

Today I want to look at upset victories/wins. My definition of an upset is based on bookmaker odds, not on ranking or any other statistics. Bookmaker odds reflect the best guess for the outcome of a match in an efficient market, since they not only take into account the ranking of the two players or their form, but also factors such as the surface, head to head outcomes between the two players and more. Therefore, an upset win can be defined as a win of a player with odds greater than a threshold, let’s say 3 (= Implied Probability roughly 30%, adjusted for vig). 

Firstly, I filter the data to only include players with at least 20 completed matches. Secondly, I exclude players with less than 5 upset wins. Then I start with looking at upset wins with a threshold odd of 3, so every win of a player with odds &gt;3 qualifies as upset win. Since surprises tend to scale with matches played, I rank the outcome by the percentage of upset wins to total matches the player entered as an underdog with odds &gt;3.

Most players making the top 50 of that statistics are ‘newer’ players. This has to do with the fact that most of the high quality data is from recent years, as explained in the Data section. Thus, upset wins from players like Novak Djokovic or Roger Federer are very unlikely, since the data is mainly from a time when they were entering almost every match as a favorite and if they were an underdog, it was typically not with odds &gt;3. 

It is straightforward to see that upset victories typically come at the early stages of the career of a tennis player. That is, when the bookmakers do not have enough information about a players skill. Once they have made some surprising wins, bookmakers lower the odds of the player in subsequent matches to reflect the updated information about their skill level more accurately. Their next wins may therefore not qualify as upset wins anymore, since the odds can be significantly lower than the threshold. This becomes obvious when looking at the odds history of a player like Carlos Alcaraz.

[Graph 1: Carlos Alcaraz ranking vs rolling median odds with a window length of 25 matches.](https://preview.redd.it/k4ugps6iyjoa1.png?width=432&amp;format=png&amp;auto=webp&amp;v=enabled&amp;s=ad92a53e46c91a5f801f8693b075dde24a266b77)

In this graph, the median odds with a rolling window of 25 matches are used. This has the advantage that the curve is smooth and a trend can be easily spotted. Median odds are used instead of average, since the average can plateau on a high level due to one match against a top opponent, for instance Nadal in the French Opens, with very high odds.

In his early days in 2019, when he was first competing in challengers and mainly futures, he often was the underdog. After quick initial success, however, he mainly entered futures tournament matches as the favorite. The same happened in challenger matches in 2020, when he dominated almost every tournament he entered. In 2021, he shifted focus to main tour events, where he often was the underdog. This is where his median odds increase again. In 2022 he had some great victories in the main tour, thus his odds decreased and are now among the lowest of all players, making him the favorite in almost any matchup.

In the following graph, we follow a simple strategy: bet 1 unit on Alcaraz whenever the odds are &gt;3. Obviously, this is with a good portion of hindsight and not a f

[... truncated, see original post ...]

**Top Comments:**

> **u/zahaha** (1 pts): As someone who just got into modeling Woman's Tennis, these are amazing. Please keep it up!

You ever look at live betting trends? Im sure its very hard to get the historical live lines but im curious if there are any situations when "if the pre match odds are &gt;-200 and the live line gets to +300, always take it", or stuff like that.
>

---

### [Odds Screen Recommendations?](https://reddit.com/r/algobetting/comments/113kr7r/odds_screen_recommendations/)
**Author**: u/zahaha | **Score**: 1 | **Comments**: 7 | **Date**: 2023-02-16

Anyone have a good odds screen that is either free or reasonably priced? The more features the better but it doesn't have to be overly complex. At the minimum I need up to date lines from the legal books and it has to include Tennis. 

Right now I am getting robbed by Oddsjam and will be cancelling my subscription this month. I like Betstamp. It is great for a free tool but does not have as many features as OddsJam. Ideally, I want something that I can easily pull into excel. A free API would be ideal. Bonus points for a site that shows low hold and arb opportunities. Would like to have live lines but don't need them.

---

## NHL / Hockey

### [I made a profit of 30000 € algobetting in 2022 - FAQ and AMA](https://reddit.com/r/algobetting/comments/10dqn0y/i_made_a_profit_of_30000_algobetting_in_2022_faq/)
**Author**: u/Hurthaba | **Score**: 32 | **Comments**: 75 | **Date**: 2023-01-16

***Quick edit:*** *Sorry for the gentleman asking for tips to not get limited in DM-chat, I accidentally clicked "ignore". Please contact me again if the answer I give in the comments is not satisfactory.*

&amp;#x200B;

I started my project 2 years ago, of which have been algo-betting with big bucks for almost a year, constantly improving my methods. My total income for betting for 2022 was 30000 euros, and with the recent improvements I have set 50k as my target for the next year. I am obviously not here to give away my secrets, but I'll gladly answer any practical questions you have. While I don't boast a 7 figure income, I'd still call myself a success since I have pretty much achieved exactly what I set out to do. And keep in mind, this is not my main profession, but a hobby, and my income is not limited to betting.

I don't do any trading or live-betting, I merely calculate pre-match probabilities very accurately and bet on where the odds exceed my calculated probability. But, what really allows me to succeed is a well thought out strategy, and I'd go as far as to say that of my method prediction algorithms are 50% and the rest is determining optimal risk etc.

&amp;#x200B;

I have had quite a few discussions of this in my private life already, as is presumable, so I gathered a lengthy F.A.Q. here already. But, I do wish to continue the discussion with someone else than myself, also, so feel free to ask away or comment. If you are interested to see graphs, I can produce some.

Also keep in mind that when I say "football" it means "soccer" in Freedom Dialect.

**"What have been your biggest wins/losses?"**

The perspective of the question is a bit off. Looking at individual wagers is meaningless, as the expected return is never going to materialize: it can only hit or miss, and not be 20% correct.

Another thing is I pretty much only bet singles, over 99.5% of the time. This is due to odds-shopping, using a number of bookmakers to guarantee the best possible odds for each wager (or, at least I used to, more on this later...). To have a longer bet slip would mean centralizing bets in a single bookmaker, possibly losing on odds.

However, at some rare cases in smaller sports, such as floorball or beach volleyball, there have been cases where my all bets have landed on the same bookmaker, in which case having them as triples etc. has been possible. The biggest wins have come from these, when the odds have multiplied. I'd say the biggest has been a long slip of quadruples in beach volleyball, resulting in 3k profit.

Because this is not wallstreetbets using derivatives, biggest loss can only be the wager placed, and that, again, has been calculated so that my risk is always optimal. It does hurt sometimes to see a 500 € bet miss, but it balanced by other bets winning: there is no point in looking at individual wagers. I don't consider any calculated bet a loss, it just the cost of doing business.

There have been cases of me failing to follow the instructions laid by my calculations, placing incorrect bets, which have caused some losses. Nothing too major in the grand scheme of things, and after each I have learned to be more focused. These are far from numerous, and could be accounted as the "cost-of-doing-business" as well. Biggest was handicap wager, where I put an extra 0 in the end, making a small 30 € bet in to 300 €, which missed, and an over/under where selected the wrong outcome at 150 €. So my losses from my "operational mistakes" have not been too bad overall.

One which does irk, though, is when I had a longish beach volley slip of doubles or triples and I selected one match winner wrong. Had I picked it correctly, I would had won almost 2k more, which would had been a significant amount of money back then when I had just started.

**"How long did it take to be profitable?"**

I did not put a single cent in betting until I knew for certain that what I did was profitable by backtesting and calculating confidence intervals. I'll answer this with the general timeline.

Day 0 of coding was around December 2020 and I made my first deposits in May 2021. The wagers were very low, like 10 cent per wager, just for getting used to the interfaces etc. The unfortunate thing was, that summer is not exactly the season for ball sports, so my volume was very low. As the autumn came I had built the confidence to raise my wagers somewhat, but I still wasn't making any sort of real bank: maybe 200-300 € per month.

All this time the algorithms had been slowly improving, but the pivotal heureka for forecasting accuracy came in March 2022 causing my income to jump substantially, and I put all my cash in. During the summer of 2022 I also perfected the calculations for suitable risk and was able to lower my ROI while increasing the volume, resulting in higher absolute income while being better diversified.

So in short: I was never losing money, but started to actually generate wealth after \~14 months of starting fr

[... truncated, see original post ...]

**Top Comments:**

> **u/weeblackskelf** (5 pts): Can you recommend any books / websites that were especially helpful in building your algorithm? I’m just barely beginning to learn python but would like to have something running in ~2 years.
>
> **u/boardsteak** (4 pts): Can you provide a cash flow for one of your accounts (e.g. bet365) from onset to limitation?
>
> **u/Hurthaba** (3 pts): I don't wish to be offensive, but betting everything sounds like gambling to me. You should at least familiarize yourself with this concept:
https://en.wikipedia.org/wiki/Kelly_criterion
>
> **u/Hurthaba** (3 pts): No idea, I am pretty set on the idea that this is not eternal. But at least Pinnacle advertises itself as never limiting accounts, and there are a couple of other bookies that I have no found evidence of limiting, even if they don't pride themselves with it. Maybe betting exchanges will someday be the solution, I don't know. But as it stands, Pinnacle is where I'm at.
>
> **u/Hurthaba** (3 pts): Are you sure you approach is correct? You can hope for the exact data you need to show up somewhere, but what it doesn't? Are you unable to create your model then? My principle has always been to gather data and see what I can do with it, not the other way around. None of my models use any "fancy" data, since it is only available for highest leagues, in which case the model would be unusable in 95 % of the matches.

I'm not saying you are doing it wrong, the point is to do things differently than others, but I'd be careful if I were you. Besides, if the information is easily attainable from an API, I can guarantee you somebody is already using it as efficiently as is possible, so you got a hell of a race ahead.
>
> **u/Hurthaba** (3 pts): I did my uni's most basic programming and data science e-courses at beginning, and from that on it has been all Stack Overflow. Not the most professional answer, but you do learn a lot by just doing. I'd say the most important thing is to get a shallow overview of what is possible and learn the vocabulary, so that you can start googling relevant topics yourself.

The programming part is quite secondary, IMO. The math behind has been much more crucial. If you just start noodling around, you'll eventually learn to code by accident, but statistics won't stick unless you really study it, and you only really need like 2 courses worth of basics for 99% of the problems you face.

Sorry for a general answer, but I can't pinpoint any particular resources.
>
> **u/Hurthaba** (3 pts): Bet365 only provides history for 6 months back (in a JavaScript-heavy web-view) and I got limited in autumn. I have contacted them and asked for more as a .csv but they just answer that "you can see last 6 months in your account history, that's it". Which is a shame, I would had liked it too.

As for the others I've been limited in, they total amount stakes were so low (like 1 or 2 % of my total turnover) that they are not very interesting and I have not bothered to gather per bet data. It does not seem there is any logic in getting limited. Were you interested in just spotting a trend which gets you limited, or my general betting? Because for the former, I'm afraid there is no answer, and believe me, I've tried to formulate one.
>
> **u/theacorneater** (3 pts): Thanks for the self ama. Where do you get data from for football?
>
> **u/Hurthaba** (2 pts): Confidence intervals, Kelly criterion, pessimistic simulations; it is very complex, but that's why it is automated. I have programmed a method and now I just bet what it tells me. There is nothing in sorts of "okay I've lost 4 bets, now I must reduce my bets", but it is linked to my current net worth at all times.

If I were to write everything I have done, this part would be 80% of the story. Modelling is "easy", there are only correct and incorrect answers, but "how much to bet on what based on what" is open for opinions.
>
> **u/Hurthaba** (2 pts): I used Pinnacle form the start, and even then it had the most bets, them having a great selection of wagers being the leading reason. The ROI at Pinnacle is slightly worse than at others, cause they sure are the sharpest, but even they won't go against the market: if more people have bet on the Home winning, they must lower those odds and raise Away, and if the public is wrong, I win. Pinnacle is just a middleman. I am not beating Pinnacle, I beat the market.
>

---

### [Anyone know the status of MySportsFeeds.com?](https://reddit.com/r/algobetting/comments/105q4et/anyone_know_the_status_of_mysportsfeedscom/)
**Author**: u/postrema19 | **Score**: 2 | **Comments**: 4 | **Date**: 2023-01-07

Hi All.  Long time lurker/first time poster.  I have a background as software developer and am very interested in this space, but am finding it difficult locating a good source of historical data and/or feeds.

I  recently stumbled across what looked to be a promising API provider at [MySportsFeeds.com](https://MySportsFeeds.com), but have found them to be unresponsive.   The API and data modeling seem to be pretty mature and well organized, but I recently found that it is not returning data for NCAAM basketball, so I'm beginning to wonder if this site is now defunct.

Does anyone have any insight into the status of this provider?  If not, any recommendations in terms of other providers in this area would be well appreciated.  I am primarily interested in data for the "big four" of the US (NFL, MLB, NBA and NHL) as well as college basketball data.

Any help or direction is greatly appreciated!

---

## Getting Started & Beginner Advice

### [Perfecting an arbitrage strategy?](https://reddit.com/r/algobetting/comments/106vhql/perfecting_an_arbitrage_strategy/)
**Author**: u/Quirky-Discount6828 | **Score**: 13 | **Comments**: 8 | **Date**: 2023-01-08

Hi, I’m new to this sub. I’ve been working on an arbitrage script and looking for suggestions or alternative strategies for arbitrage betting.

Here is an example of what my script is currently doing. Any suggestions or recommendations are welcomed!

Edit: if anyone has any good ideas and would like to work together I’m open to that too.

[Arb script example](https://ibb.co/sj4Wj9v)

**Top Comments:**

> **u/MathyBets** (6 pts): You won’t find much worthwhile on the odds api. They don’t do non-mainline markets and only just started player props. Their refresh rate on most lines, especially player props, are too slow to find any meaningful arbs.

The issue you’ll have with a bot doing this is what happens when lines change mid bet, which they will do, especially if you use stale lines like odds api has. For example, if odds change and it’s no longer an arb, so you no longer want to place the bets? Still place the bets and lose money, since it’s not an arb? Place one side and hedge later? These logic loops get complex and will depend on the magnitude of the odds change.

I run an arb service via scraping and buying data feeds - which you’ll have to do if you want to be serious about it. 

I’m happy to chat. I’ve been arbing, +EV, and math betting before it was “cool”.
>
> **u/Quirky-Discount6828** (6 pts): I’m only using 5 books (the ones I can access) which is really the main problem… and I’m using theoddsapi
>
> **u/PythonVillage** (3 pts): My two cents: there are so few arb opportunities that the only way you could catch enough of them to make this worth while is to have the code running all day every day. But, given that the API will rate limit you, I think it’s a fools errand
>
> **u/PythonVillage** (3 pts): Which books &amp; APIs are you using to pull your data?
>
> **u/Quirky-Discount6828** (2 pts): Yup I completely agree and that’s pretty much what led me to making this post. I’m just trying to find a plausible method that I can automate for fun
>
> **u/JimmyRazzo75** (1 pts): I would try finding an edge in a sports market big enough that you can profit comfortably without getting immediately limited.
>
> **u/kecepa5669** (1 pts): Hi, I currently run the r/OddsWire subreddit. I was wondering if you might find any of the data there useful and/or have any suggestions how we might make the data there more useful for your purposes? We pull data feeds from all the sportsbooks.
>
> **u/Quirky-Discount6828** (1 pts): Ya I’ve noticed that with the odds api. Sometimes it works fine but it’s definitely not super reliable.
>

---

### [Hi, I'm the founder of Sporttrade, a sports betting exchange in New Jersey.](https://reddit.com/r/algobetting/comments/10pn1ri/hi_im_the_founder_of_sporttrade_a_sports_betting/)
**Author**: u/sporttrade | **Score**: 11 | **Comments**: 29 | **Date**: 2023-01-31

Hi reddit,

My name is Alex Kane, and I'm the founder and ceo of Sporttrade.

Before you read this, yes, this is an ad. But it's not one where we hope to earn a bunch of downloads. Instead, my hope is to connect with some of you directly about our product and how you can use it to your advantage.

**A bit about me**

I started Sporttrade in 2018, before sports betting was legal in New Jersey. I didn't really know much about betting at the time. My goal was to create an app that combined betting and trading.

Sometime in 2019, I figured I would try placing a bet. I had followed Captain Jack on twitter, and he had mentioned something about bonus arbitrage. At that time, there were 15 sportsbooks in NJ, all offering $250+ for new players. So, I paired up with my buddy, a math teacher, and set out to NJ to try and take advantage of the bonuses.

Several trips to new States and a few overdrafts of my checking account later, I felt like I had done well to take advantage of various offers, VIP programs, and learned a lot about the industry.

While the perils of online casino ultimately cost me a few thousand 🙄 , I still came out on top, with my profits topping my Sporttrade salary some years! (Pikkit record attached)

**Arbing signup bonuses**

As many of you know, there's a significant profit opportunity presented by the numerous sign-up offers at books like DK and FD.

In short, it looks like this:

Draftkings offers a $1,000 risk free first bet. If the bet loses, you get a $1,000 bet credit back. So, you place a bet on something like "Giants Moneyline" at 3/1 odds on DK, and then "Eagles Moneyline" at 1/3 odds on Fanduel.

Either way, you win/lose $0, but if the Giants lose, DK gives you a $1000 bet credit. You then place another bet "pair" ($1000 bet credit on DK, and an offsetting bet on Pointsbet) to turn that $1,000 credit into cash.

...then onto the next welcome offer.

**What is Sporttrade?**

As I learned more arb betting, I began to realize how beneficial a betting exchange could be to arbitrage bettors. In fact, some of our biggest customers are doing just that; arbing prices and offers of other venues.

Here are some qualities about Sporttrade that make it a must-have for arbers:

➡️ Really tight pricing (as good as -103/-103 on a 50/50 bet)➡️ Transparent limits, and great liquidity (several thousand $ available)➡️ No delays, and instant re-bets

**My offer to you:**

In talking to many of our customers, I realize that while most folks have taken advantage of DK, FD, MGM, PointsBet, CZR offers, they haven't done the same for Betway, WynnBet, Superbook, etc.

So, if any of you are up for it, I'd be more than happy to set up time to meet, introduce you to Sporttrade, and help you use us to get the most out of your betting, whether you're an arbing beginner, or looking to take your game to the next level. My number is below.

Your first bet on Sporttrade is risk free, up to $300 (so I can help you arb that!), and thanks to our partnership with Unabated and OddsJam, you can get access to those tools at a significant discount.

Thanks for reading, and looking forward to connecting with some of you!

Alex(484) 678-8791

**Edit:** You can download the app here:   
https://apps.apple.com/us/app/sporttrade/id1525381125

&amp;#x200B;

[2021 Pikkit Record \(my last year of arbing\)](https://preview.redd.it/j6gn58gzsafa1.jpg?width=1242&amp;format=pjpg&amp;auto=webp&amp;v=enabled&amp;s=795a6562baf0183c81e9825f8921e0739339050b)

**Top Comments:**

> **u/Ok-Seaworthiness3874** (2 pts): Cool idea, and looks like great execution (sorry I'm not in NJ so I can't check), but do you offer e-sports betting? It is VERY difficult to find US based books (Maybe not any tbh, some have only like Super S tier events only) that offer comprehensive offerings of e-sports (it's basically just bovada which is very grey-market, but legit, and thank god for them). 

Considering the MASSIVE growth in e-sports, and especially appealing to a young demographic that probably isn't into traditional sports typically - would you consider adding it?

I'm a bit of a Dota 2 sharp (game with yearly 40M prize pools for players, shit aint no joke) and am on my probably 10th bovada account. Thinking about moving states because the lack of opportunity to bet is frustrating.
>
> **u/SOGorman35** (2 pts): 1) not really a question but I hate you because I had an idea for an exchange like SportTrade (before I knew anything about sports betting) only to discover that it already existed.  I'm definitely rooting for you to succeed.
2) Ohio anytime soon?
3) I know you have said that there are multiple marker makers lined up, and I wouldn't expect you to necessarily identify them, but are any of the MMs affiliated with SportTrade?  I know that Nadex and Kalshi both have affiliates or subsidiaries that function as the primary MMs in their exchanges, so I'm half assuming this is the case here.
>
> **u/afk_again** (2 pts): This looks interesting.  Are there plans to support horse racing?  Also can you post again when there's API access.  A swagger page would be nice too.
>
> **u/Fly-iggles-fly** (1 pts): Is Spanky one of your market makers?
>
> **u/Artistic_Dog_** (1 pts): Hey Alex, how is this developing? Do you have a trading API or connection to trading software like Bet Angel or GeeksToy? Super interested on this
>
> **u/sporttrade** (1 pts): Now in NJ/CO/IA/AZ/VA, we’d like to launch in:

IN/MD/KY/NC/MI/IL/PA/OH/MO/WV/LA/MA/KS

although some of those states will require some legislative changes
>
> **u/madtadder** (1 pts): I reached out to them directly in February, and they said "We haven’t made available our pricing api to individuals just yet. Once we do that, we fear the floodgates will open and we would need to rebuild our market data endpoint service to handle the load" which is sorta hilarious since they claim to have an API that's available
>
> **u/random-50** (1 pts): Any trading api yet, or imminent?

What’s the pipeline of states?
>
> **u/poubelleaccount** (1 pts): I don't see much liquidity on [https://markets.getsporttrade.com/nj](https://markets.getsporttrade.com/nj); for instance, there doesn't seem to be a market on the Pacers game today. Is that a bug?
>
> **u/OliverAlden** (1 pts): Thanks.  Just discovered sports trade which is new to my state.
>

---

### [Common Questions](https://reddit.com/r/algobetting/comments/119hp1j/common_questions/)
**Author**: u/zahaha | **Score**: 10 | **Comments**: 4 | **Date**: 2023-02-22

TLDR: What are the main questions that you have/had as a beginner and what resources are you looking for but hard to find?

I am relatively new to Algo betting and have not found it easy to find good resources around modeling, statistical strategies, programming, etc.  I think that a consolidated list of all kinds of resources could benefit everyone.

I have started to keep a small list myself and would like to build it out to include a wide variety of topics. I will make it public so everyone can view it. But first I want to compile a list of Topics. What are other topics related to all things Algobetting that should be included on this list? This is what I have so far:

**Programming**

* Python/R
* Learn Python/R
* Data Scraping
* Prewritten Code Sets

**Data**

* Best resources for historical stats, box scores, Odds, etc by sport
* Best resources for current market odds
* Odds Screens
* API's

**Models and Statistics**

* Resources for Learning about statistics (particularly those relevant to sports modeling) 
* Types of Models
* Examples by sport

**Best Media Related to Sports Betting and Modeling** 

* YouTube Videos
* Podcasts
* Books
* Articles/Blogs
* Twitter Follows

**Top Comments:**

> **u/zahaha** (2 pts): Yep, I've seen this pinned post and its a good starting point. However it's lacking resources for many of the common questions and isn't organized. 

I would like to improve on this with a more comprehensive and organized list.
>
> **u/stander414** (2 pts): https://www.reddit.com/r/algobetting/comments/g5hi6j/creating_a_collection_of_resources_to_introduce
>
> **u/ENTP_Geek** (1 pts): How is this going? Have you added much to your list?
>

---

## Arbitrage & Sure Bets

### [Perfecting an arbitrage strategy?](https://reddit.com/r/algobetting/comments/106vhql/perfecting_an_arbitrage_strategy/)
**Author**: u/Quirky-Discount6828 | **Score**: 13 | **Comments**: 8 | **Date**: 2023-01-08

Hi, I’m new to this sub. I’ve been working on an arbitrage script and looking for suggestions or alternative strategies for arbitrage betting.

Here is an example of what my script is currently doing. Any suggestions or recommendations are welcomed!

Edit: if anyone has any good ideas and would like to work together I’m open to that too.

[Arb script example](https://ibb.co/sj4Wj9v)

**Top Comments:**

> **u/MathyBets** (6 pts): You won’t find much worthwhile on the odds api. They don’t do non-mainline markets and only just started player props. Their refresh rate on most lines, especially player props, are too slow to find any meaningful arbs.

The issue you’ll have with a bot doing this is what happens when lines change mid bet, which they will do, especially if you use stale lines like odds api has. For example, if odds change and it’s no longer an arb, so you no longer want to place the bets? Still place the bets and lose money, since it’s not an arb? Place one side and hedge later? These logic loops get complex and will depend on the magnitude of the odds change.

I run an arb service via scraping and buying data feeds - which you’ll have to do if you want to be serious about it. 

I’m happy to chat. I’ve been arbing, +EV, and math betting before it was “cool”.
>
> **u/Quirky-Discount6828** (6 pts): I’m only using 5 books (the ones I can access) which is really the main problem… and I’m using theoddsapi
>
> **u/PythonVillage** (3 pts): My two cents: there are so few arb opportunities that the only way you could catch enough of them to make this worth while is to have the code running all day every day. But, given that the API will rate limit you, I think it’s a fools errand
>
> **u/PythonVillage** (3 pts): Which books &amp; APIs are you using to pull your data?
>
> **u/Quirky-Discount6828** (2 pts): Yup I completely agree and that’s pretty much what led me to making this post. I’m just trying to find a plausible method that I can automate for fun
>
> **u/JimmyRazzo75** (1 pts): I would try finding an edge in a sports market big enough that you can profit comfortably without getting immediately limited.
>
> **u/kecepa5669** (1 pts): Hi, I currently run the r/OddsWire subreddit. I was wondering if you might find any of the data there useful and/or have any suggestions how we might make the data there more useful for your purposes? We pull data feeds from all the sportsbooks.
>
> **u/Quirky-Discount6828** (1 pts): Ya I’ve noticed that with the odds api. Sometimes it works fine but it’s definitely not super reliable.
>

---

### [Hi, I'm the founder of Sporttrade, a sports betting exchange in New Jersey.](https://reddit.com/r/algobetting/comments/10pn1ri/hi_im_the_founder_of_sporttrade_a_sports_betting/)
**Author**: u/sporttrade | **Score**: 11 | **Comments**: 29 | **Date**: 2023-01-31

Hi reddit,

My name is Alex Kane, and I'm the founder and ceo of Sporttrade.

Before you read this, yes, this is an ad. But it's not one where we hope to earn a bunch of downloads. Instead, my hope is to connect with some of you directly about our product and how you can use it to your advantage.

**A bit about me**

I started Sporttrade in 2018, before sports betting was legal in New Jersey. I didn't really know much about betting at the time. My goal was to create an app that combined betting and trading.

Sometime in 2019, I figured I would try placing a bet. I had followed Captain Jack on twitter, and he had mentioned something about bonus arbitrage. At that time, there were 15 sportsbooks in NJ, all offering $250+ for new players. So, I paired up with my buddy, a math teacher, and set out to NJ to try and take advantage of the bonuses.

Several trips to new States and a few overdrafts of my checking account later, I felt like I had done well to take advantage of various offers, VIP programs, and learned a lot about the industry.

While the perils of online casino ultimately cost me a few thousand 🙄 , I still came out on top, with my profits topping my Sporttrade salary some years! (Pikkit record attached)

**Arbing signup bonuses**

As many of you know, there's a significant profit opportunity presented by the numerous sign-up offers at books like DK and FD.

In short, it looks like this:

Draftkings offers a $1,000 risk free first bet. If the bet loses, you get a $1,000 bet credit back. So, you place a bet on something like "Giants Moneyline" at 3/1 odds on DK, and then "Eagles Moneyline" at 1/3 odds on Fanduel.

Either way, you win/lose $0, but if the Giants lose, DK gives you a $1000 bet credit. You then place another bet "pair" ($1000 bet credit on DK, and an offsetting bet on Pointsbet) to turn that $1,000 credit into cash.

...then onto the next welcome offer.

**What is Sporttrade?**

As I learned more arb betting, I began to realize how beneficial a betting exchange could be to arbitrage bettors. In fact, some of our biggest customers are doing just that; arbing prices and offers of other venues.

Here are some qualities about Sporttrade that make it a must-have for arbers:

➡️ Really tight pricing (as good as -103/-103 on a 50/50 bet)➡️ Transparent limits, and great liquidity (several thousand $ available)➡️ No delays, and instant re-bets

**My offer to you:**

In talking to many of our customers, I realize that while most folks have taken advantage of DK, FD, MGM, PointsBet, CZR offers, they haven't done the same for Betway, WynnBet, Superbook, etc.

So, if any of you are up for it, I'd be more than happy to set up time to meet, introduce you to Sporttrade, and help you use us to get the most out of your betting, whether you're an arbing beginner, or looking to take your game to the next level. My number is below.

Your first bet on Sporttrade is risk free, up to $300 (so I can help you arb that!), and thanks to our partnership with Unabated and OddsJam, you can get access to those tools at a significant discount.

Thanks for reading, and looking forward to connecting with some of you!

Alex(484) 678-8791

**Edit:** You can download the app here:   
https://apps.apple.com/us/app/sporttrade/id1525381125

&amp;#x200B;

[2021 Pikkit Record \(my last year of arbing\)](https://preview.redd.it/j6gn58gzsafa1.jpg?width=1242&amp;format=pjpg&amp;auto=webp&amp;v=enabled&amp;s=795a6562baf0183c81e9825f8921e0739339050b)

**Top Comments:**

> **u/Ok-Seaworthiness3874** (2 pts): Cool idea, and looks like great execution (sorry I'm not in NJ so I can't check), but do you offer e-sports betting? It is VERY difficult to find US based books (Maybe not any tbh, some have only like Super S tier events only) that offer comprehensive offerings of e-sports (it's basically just bovada which is very grey-market, but legit, and thank god for them). 

Considering the MASSIVE growth in e-sports, and especially appealing to a young demographic that probably isn't into traditional sports typically - would you consider adding it?

I'm a bit of a Dota 2 sharp (game with yearly 40M prize pools for players, shit aint no joke) and am on my probably 10th bovada account. Thinking about moving states because the lack of opportunity to bet is frustrating.
>
> **u/SOGorman35** (2 pts): 1) not really a question but I hate you because I had an idea for an exchange like SportTrade (before I knew anything about sports betting) only to discover that it already existed.  I'm definitely rooting for you to succeed.
2) Ohio anytime soon?
3) I know you have said that there are multiple marker makers lined up, and I wouldn't expect you to necessarily identify them, but are any of the MMs affiliated with SportTrade?  I know that Nadex and Kalshi both have affiliates or subsidiaries that function as the primary MMs in their exchanges, so I'm half assuming this is the case here.
>
> **u/afk_again** (2 pts): This looks interesting.  Are there plans to support horse racing?  Also can you post again when there's API access.  A swagger page would be nice too.
>
> **u/Fly-iggles-fly** (1 pts): Is Spanky one of your market makers?
>
> **u/Artistic_Dog_** (1 pts): Hey Alex, how is this developing? Do you have a trading API or connection to trading software like Bet Angel or GeeksToy? Super interested on this
>
> **u/sporttrade** (1 pts): Now in NJ/CO/IA/AZ/VA, we’d like to launch in:

IN/MD/KY/NC/MI/IL/PA/OH/MO/WV/LA/MA/KS

although some of those states will require some legislative changes
>
> **u/madtadder** (1 pts): I reached out to them directly in February, and they said "We haven’t made available our pricing api to individuals just yet. Once we do that, we fear the floodgates will open and we would need to rebuild our market data endpoint service to handle the load" which is sorta hilarious since they claim to have an API that's available
>
> **u/random-50** (1 pts): Any trading api yet, or imminent?

What’s the pipeline of states?
>
> **u/poubelleaccount** (1 pts): I don't see much liquidity on [https://markets.getsporttrade.com/nj](https://markets.getsporttrade.com/nj); for instance, there doesn't seem to be a market on the Pacers game today. Is that a bug?
>
> **u/OliverAlden** (1 pts): Thanks.  Just discovered sports trade which is new to my state.
>

---

### [Data source (API) - Arbitrage betting](https://reddit.com/r/algobetting/comments/1fn851s/data_source_api_arbitrage_betting/)
**Author**: u/OogyBoogyMen | **Score**: 2 | **Comments**: 3 | **Date**: 2024-09-23

Hi, I am currently collecting data over a specific online Casino, CloudBet, in oprder to test some arbitrage strategies. They give access to their API for free which makes itt super easy to gather whatever info I need.

I am looking to collect the same data but from other SportsBooks to compare the odds the provide and the volatility of their changes. 

Would anyone be able to suggest me or would have already tested another API to some other bookies?

Guidance would be appreciated since all these API that pop up online for eg. Bet365 seem old and they all cost money, so I don't want to end up paying for something that's not up anymore.

Thank you all

---

### [Odds Screen Recommendations?](https://reddit.com/r/algobetting/comments/113kr7r/odds_screen_recommendations/)
**Author**: u/zahaha | **Score**: 1 | **Comments**: 7 | **Date**: 2023-02-16

Anyone have a good odds screen that is either free or reasonably priced? The more features the better but it doesn't have to be overly complex. At the minimum I need up to date lines from the legal books and it has to include Tennis. 

Right now I am getting robbed by Oddsjam and will be cancelling my subscription this month. I like Betstamp. It is great for a free tool but does not have as many features as OddsJam. Ideally, I want something that I can easily pull into excel. A free API would be ideal. Bonus points for a site that shows low hold and arb opportunities. Would like to have live lines but don't need them.

---

## General Discussion

### [Daily Betting Journal](https://reddit.com/r/algobetting/comments/1k7ok2u/daily_betting_journal/)
**Author**: u/AutoModerator | **Score**: 2 | **Comments**: 2 | **Date**: 2025-04-25

Post your picks, updates, track model results, current projects, daily thoughts, anything goes.

---

### [Exact bet here.. I wanna hit](https://reddit.com/r/algobetting/comments/1kbbkeu/exact_bet_here_i_wanna_hit/)
**Author**: u/Maleficent_Pea8874 | **Score**: 1 | **Comments**: 5 | **Date**: 2025-04-30

---

### [Tips for automatic interaction with websites](https://reddit.com/r/algobetting/comments/1k62o55/tips_for_automatic_interaction_with_websites/)
**Author**: u/Flewizzle | **Score**: 1 | **Comments**: 4 | **Date**: 2025-04-23

Hey guys im building a bot to place bets on 365 for me automatically using a data feed, and im wondering, when acting on an advised bet from the feed, would you recommend starting at the homepage and using automation to navigate (homepage &gt;&gt; greyhound racing &gt;&gt; specific race), or simply going directly to the race via URL?

Also, do you think its better for the chrome session to be with a signed in chrome account?

does anyone have any extra tips? im using an anti detection browser set up and trying to mimic natural mouse movements.

---

### [UFC BETTING EXPERT](https://reddit.com/r/algobetting/comments/1k7saln/ufc_betting_expert/)
**Author**: u/[deleted] | **Score**: 0 | **Comments**: 6 | **Date**: 2025-04-25

---
