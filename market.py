from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
import random
import numpy as np
class Security:
    def __init__(self, name, initial_price, shares_outstanding):
        self.name = name
        self.price = initial_price
        self.shares_outstanding = shares_outstanding
        self.price_history = [initial_price]
    
    def update_price(self):
        price_change = random.gauss(0, 0.02) * self.price
        self.price = max(0.01, self.price + price_change)
        self.price_history.append(self.price)
    
    def market_cap(self):
        return self.price * self.shares_outstanding


class InvestorAgent(Agent):
    def __init__(self, unique_id, model, strategy, initial_cash=10000):
        super().__init__(unique_id, model)
        self.strategy = strategy
        self.cash = initial_cash
        self.portfolio = {}
    
    def step(self):
        for security in self.model.securities:
            action, shares = self.strategy.decide(security, self)
            if action == "buy":
                cost = shares * security.price
                if cost <= self.cash:
                    self.cash -= cost
                    self.portfolio[security] = self.portfolio.get(security, 0) + shares
            elif action == "sell" and security in self.portfolio:
                if self.portfolio[security] >= shares:
                    self.cash += shares * security.price
                    self.portfolio[security] -= shares
                    if self.portfolio[security] == 0:
                        del self.portfolio[security]
                        
    def portfolio_value(self):
        stock_value = sum(security.price * shares for security, shares in self.portfolio.items())
        return self.cash + stock_value


class TrendFollower:
    def __init__(self, lookback=5):
        self.lookback = lookback
    
    def decide(self, security, investor):
        if len(security.price_history) < self.lookback + 1:
            return "hold", 0
        
        recent_prices = security.price_history[-self.lookback:]
        if recent_prices[-1] > recent_prices[0]:
            shares_to_buy = int(investor.cash / security.price * 0.1)
            return "buy", shares_to_buy
        elif recent_prices[-1] < recent_prices[0]:
            shares_to_sell = investor.portfolio.get(security, 0) // 2
            return "sell", shares_to_sell
        
        return "hold", 0
    
    def mutate(self):
        new_lookback = max(1, self.lookback + random.choice([-1, 0, 1]))
        return TrendFollower(lookback=new_lookback)

class RLStrategy:
    def __init__(self, learning_rate=0.1, discount_factor=0.95, exploration_rate=0.1, lookback=5):
        self.q_table = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.lookback = lookback

    def decide(self, security, investor):
        state = (tuple(security.price_history[-self.lookback:]), investor.cash)
        actions = ["buy", "sell", "hold"]

        q_values = self.q_table.get(state, {a: 0 for a in actions})
        if np.random.rand() < self.exploration_rate:
            action = np.random.choice(actions)
        else:
            action = max(q_values, key=q_values.get)

        reward = investor.portfolio_value() - sum(security.price * shares for security, shares in investor.portfolio.items())
        self.q_table[state] = self.q_table.get(state, {a: 0 for a in actions})
        self.q_table[state][action] += self.learning_rate * (reward + self.discount_factor * max(q_values.values()) - self.q_table[state][action])

        return action, investor.cash // security.price if action == "buy" else investor.portfolio.get(security, 0)

    def mutate(self):
        new_learning_rate = max(0.01, self.learning_rate + random.choice([-0.01, 0, 0.01]))
        new_discount_factor = min(1.0, max(0.8, self.discount_factor + random.choice([-0.01, 0, 0.01])))
        new_exploration_rate = min(1.0, max(0.01, self.exploration_rate + random.choice([-0.01, 0, 0.01])))
        new_lookback = max(1, self.lookback + random.choice([-1, 0, 1]))
        return RLStrategy(
            learning_rate=new_learning_rate,
            discount_factor=new_discount_factor,
            exploration_rate=new_exploration_rate,
            lookback=new_lookback
        )


class StockMarketModel(Model):
    def __init__(self, num_investors=5, securities=None, width=10, height=10):
        super().__init__()
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(width, height, torus=True)
        self.securities = securities if securities else [
            Security("ACME Corp.", 150, 1_000_000),
            Security("Widgets Conglomerated Inc.", 700, 500_000),
        ]

        self.generation = 0

        for i in range(num_investors):
            stragies = [TrendFollower(lookback=random.randint(3, 7)), RLStrategy()]
            investor = InvestorAgent(i, self, strategy=random.choice(stragies))
            self.schedule.add(investor)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(investor, (x, y))

        self.datacollector = DataCollector(
            model_reporters={f"{security.name} Market Cap": lambda m, sec=security: sec.market_cap() for security in self.securities},
            agent_reporters={"Portfolio Value": lambda a: a.portfolio_value() if isinstance(a, InvestorAgent) else 0}
        )

    def reproduce(self):
        investors = sorted(self.schedule.agents, key=lambda a: a.portfolio_value(), reverse=True)
        top_investors = investors[:len(investors)//2]

        new_agents = []
        for i, parent in enumerate(top_investors):
            new_strategy = parent.strategy.mutate() 
            new_agent = InvestorAgent(i + len(self.schedule.agents), self, strategy=new_strategy)
            new_agents.append(new_agent)

        for old_agent in investors[len(investors)//2:]:
            self.schedule.remove(old_agent)

        for new_agent in new_agents:
            self.schedule.add(new_agent)


    def step(self):
        print("Market Caps:", [security.market_cap() for security in self.securities])
        for security in self.securities:
            security.update_price()

        self.schedule.step()
        self.datacollector.collect(self)

        if self.schedule.steps % 10 == 0:
            self.reproduce()



def agent_portrayal(agent):
    if isinstance(agent, InvestorAgent):
        portrayal = {
            "Shape": "circle",
            "Color": "blue",
            "r": 0.5,
            "Layer": 0,
            "text": f"Cash: {agent.cash:.2f}\nPortfolio: {[(sec.name, shares) for sec, shares in agent.portfolio.items()]}",
            "text_color": "black",
        }
        return portrayal
    return {}


grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)
def create_chart_module(securities):
    chart_data = [{"Label": f"{security.name} Market Cap", "Color": "Red"} for security in securities]
    return ChartModule(chart_data, data_collector_name="datacollector")

securities = [
    Security("ACME Corp.", 150, 1_000_000),
    Security("Widgets Conglomerated Inc.", 700, 500_000),
]

server = ModularServer(
    StockMarketModel,
    [grid, create_chart_module(securities)],
    "Stock Market Model",
    {"num_investors": 5},
)

server.port = 8521 
server.launch()