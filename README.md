# ABMMarket
###### Agent Based Model Market

![Screenshot](https://cloud-axn42ccrb-hack-club-bot.vercel.app/0image.png)

You can access a demo at [my VPS](http://45.55.228.84:8521/). PLEASE BE GENTLE ON IT, AND STOP ASAP. I do not have a lot of bandwidth.

This an agent based model with a webui, that simulates a stock market, with several traders, each with different portfolios, trading on several stocks. The traders evolve, with their models being modified based on new data every so often. By default, it contains 2 stocks, however it is relatively trivial to add more to it.

While this is not an exact replica of the stock market, it should be a pretty good comparison, due to the large amount of trend followers acting a lot like retail investors, and RL investors acting more like proper funds and the like.

Running:
- Install the following libraries: mesa==2.3.1 & numpy
- Run it with python market.py
- A webui should automatically open, and if it doesn't, then go to 127.0.0.1:8521 in your browser. Then press start, and you can watch it!

If you want to add more securities, you can go to the list `securities` inside of `market.py`, and add more. Currently it only has `ACME Corp.` and `Widgets Conglomerated Inc.`

If you want to add more investors, than go to line 193, and modify `num_investors`. If you make `num_investors` exceed 100, then expand the CanvasGrid in line 179, setting it to whatever you need to make it possible to view all the investors. The second and third params are width and height. 

Explanation of the models:

TrendFollower: This looks for the momentum in a stock, and if it is trending upward, it buys it, and if it's trending downwards, it sells it. In the real world, this is mostly a retail investor, and tends to lead to extreme endogenous fluctuations from an equilibrium, due to the aggressiveness of its movement (ie it makes stocks way over- or under- valued). 

RL: This is more algorithmic, and tries stuff, and either gets a reward or punishment, depending on whether whatever it tries succeeds or fails, leading to more accurate predictions than mere trend following.                                                                                                                              