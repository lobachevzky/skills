"""
the algorithm
"""
# stdlib
import argparse

# third party
from gym.wrappers import TimeLimit
import numpy as np
import plotly
import plotly.graph_objs as go

# first party
from skills.gridworld import GoalGridworld
from skills.trainer import Trainer


def main(iterations: int, slack: int):
    desc = [
        '____#____',
        '_________',
        '____#____',
        '#_#####_#',
        '____#____',
        '_________',
        '____#____',
    ]
    ENV = TimeLimit(
        max_episode_steps=15,
        env=GoalGridworld(
            desc=desc,
            rewards=dict(),
            terminal='T',
            start_states='_',
            blocked_states='#',
        ))
    ENV.seed(0)

    # actions=np.array([[0, 1], [0, 0], [0, -1]]),
    # action_strings="▶s◀")
    def train(baseline: bool):
        return Trainer(
            env=ENV, slack_factor=slack).train(
                iterations=iterations, baseline=baseline)

    print('baseline')
    b_x, b_y = zip(*enumerate(train(baseline=True)))
    print('experiment')
    e_x, e_y = zip(*enumerate(train(baseline=False)))
    fig = go.Figure(
        data=[
            go.Scatter(x=e_x, y=e_y, name='experiment'),
            go.Scatter(x=b_x, y=b_y, name='baseline')
        ],
        layout=dict(yaxis=dict(type='log')))
    plotly.offline.plot(fig, auto_open=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--iterations', type=int, required=True)
    parser.add_argument('-s', '--slack', type=int, required=True)
    np.random.seed(0)
    main(**vars(parser.parse_args()))
