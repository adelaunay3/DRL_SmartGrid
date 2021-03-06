import numpy as np
import matplotlib.pyplot as plt
import copy

from Env import Env, ACTIONS, BATTERY_CAPACITY
from Model import predict

"""
Strategies supported :
    - DQN
    - Nothing
    - Random
    - Trade
    - RandomBattery    # random charge/discharge
    - SmartBattery
    - SmartBattery2
"""
STRATEGIES = ["Random", "Nothing", "Trade", "RandomBattery", "SmartBattery", "SmartBattery2", "DQN"]


def strategyAction(strategy, state, DQN_model=None):
    """ 
    Determines the action of the given strategy on the state.

    Parameters: 
    strategy (str): strategy to use

    state (State): current State of the environment

    Returns: 
    action (str): action of the strategy given the state.

    """
    if strategy == "DQN":
        if DQN_model is None:
            print("No DQN model given in the function strategyAction")
            return ACTIONS[0]

        q_value = [predict(DQN_model, state, a) for a in ACTIONS]
        return ACTIONS[np.argmax(q_value)]

    if strategy == "Random":
        return np.random.choice(ACTIONS)

    if strategy == "Trade":
        return ACTIONS[-1]

    if strategy == "Nothing":
        return ACTIONS[-2]

    if strategy == "RandomBattery":
        return np.random.choice(ACTIONS[0:2])

    if strategy == "SmartBattery":
        if state.panelProd > state.consumption:
            return ACTIONS[0]
        else:
            return ACTIONS[1]

    if strategy == "SmartBattery2":
        if state.panelProd > state.consumption and state.battery < BATTERY_CAPACITY * 0.9999:
            return ACTIONS[0]
        elif state.panelProd > state.consumption:
            return ACTIONS[-1]
        else:
            return ACTIONS[1]


def test(env: Env, nb_step, DQN_model=None):
    """ 
    Displays figures to compare the result of the DQN algorithm to other predefined strategies.

    Parameters: 
    env (Env): environment on which the strategies are tested

    nb_step (int): number of steps on which to evaluate strategies

    DQN_model: the model returned by the DQN algorithm.
    If this parameter is set to None, then only the predefined strategies are tested.
    This is useful to check the environment.

    """

    env.reset(nb_step=nb_step)
    initState = copy.deepcopy(env.currentState)

    conso, prod, price = [], [], []

    actions_qvalue = {}
    for a in ACTIONS:
        actions_qvalue[a] = []

    for i in range(nb_step):
        env.step(ACTIONS[0])

        conso.append(env.currentState.consumption)
        prod.append(env.currentState.panelProd)
        price.append(env.currentState.price)

    actions, cost = {}, {}
    battery, charge, discharge, generate, trade = {}, {}, {}, {}, {}

    strategies_list = STRATEGIES[:]

    if DQN_model is None:
        strategies_list.remove("DQN")

    for strategy in strategies_list:
        actions[strategy], cost[strategy] = [], []
        (
            battery[strategy],
            charge[strategy],
            discharge[strategy],
            generate[strategy],
            trade[strategy],
        ) = ([], [], [], [], [])

        env.currentState = copy.deepcopy(initState)
        for i in range(nb_step):
            if strategy == "DQN":
                q_value = predict(DQN_model, env.currentState, ACTIONS)
                action = ACTIONS[np.argmax(q_value)]
                for q, a in zip(q_value, ACTIONS):
                    actions_qvalue[a].append(float(q))
            else:
                action = strategyAction(strategy, env.currentState)
            _, _, step_cost = env.step(action)

            cost[strategy].append(step_cost)
            actions[strategy].append(action)
            battery[strategy].append(env.currentState.battery)

            charge[strategy].append(env.currentState.charge)
            discharge[strategy].append(env.currentState.discharge)
            generate[strategy].append(env.currentState.generate)
            trade[strategy].append(env.currentState.trade)

    fig, axs = plt.subplots(len(strategies_list))
    for i, s in enumerate(strategies_list):
        axs[i].plot(trade[s])
        axs[i].plot(battery[s])
        axs[i].legend(["Trade", "Battery"])
        axs[i].title.set_text(s)
    plt.figure(1)

    fig, axs = plt.subplots(len(strategies_list))

    for i, s in enumerate(strategies_list):
        axs[i].plot(actions[s])
        axs[i].legend(["Actions"])
        axs[i].title.set_text(s)
    plt.figure(2)

    fig, axs = plt.subplots(2)
    axs[0].plot(conso)
    axs[0].plot(prod)
    axs[1].plot(price)
    axs[0].legend(["Consumption", "Production"])
    axs[1].title.set_text("Price")
    plt.figure(3)

    fig, ax = plt.subplots()
    for s in strategies_list:
        ax.plot(np.cumsum(cost[s]))

    ax.legend(strategies_list)
    ax.title.set_text("Cost")
    plt.figure(4)

    fig, ax = plt.subplots()
    for a in ACTIONS:
        ax.plot(actions_qvalue[a])
    ax.legend(ACTIONS)
    ax.title.set_text("Q-value")
    plt.figure(5)

    plt.show()
