#! /usr/bin/env python
# stdlib
import sys
import time
from collections import namedtuple
from typing import Container, Dict, Iterable, Tuple

import numpy as np
# third party
from gym import utils, spaces
from gym.envs.toy_text.discrete import DiscreteEnv, categorical_sample
from six import StringIO

Transition = namedtuple('Transition', 'probability new_state reward terminal')


class Gridworld(DiscreteEnv):
    def __init__(self,
                 desc: Iterable[Iterable[str]],
                 terminal: Container[str],
                 rewards: Dict[str, float],
                 start_states: Container[str] = '',
                 blocked_states: Container[str] = '',
                 actions: Iterable[np.ndarray] = np.array([
                     [0, 1],
                     [1, 0],
                     [0, -1],
                     [-1, 0],
                 ],
                                                          dtype=int),
                 action_strings: Iterable[str] = "▶▼◀▲"):

        self.action_strings = np.array(tuple(action_strings))
        self.desc = _desc = np.array(
            [list(r) for r in desc])  # type: np.ndarray
        nrows, ncols = _desc.shape
        self._transition_matrix = None
        self._reward_matrix = None

        def transition_tuple(i: int, j: int, action: np.ndarray
                             ) -> Tuple[float, int, float, bool]:
            letter = str(_desc[i, j])
            new_state = np.clip(
                np.array([i, j], dtype=int) + action,
                a_min=np.zeros(2, dtype=int),
                a_max=np.array(_desc.shape, dtype=int) - 1,
            )

            if _desc[tuple(new_state)] in blocked_states:
                new_state = (i, j)
            return Transition(
                probability=1.,
                new_state=self.encode(*new_state),
                reward=rewards.get(letter, 0),
                terminal=letter in terminal)

        transitions = {
            self.encode(i, j): {
                a: [transition_tuple(i, j, action)]
                for a, action in enumerate(actions)
            }
            for i in range(nrows) for j in range(ncols)
        }
        isd = np.isin(_desc, tuple(start_states))
        isd = isd / isd.sum()

        super().__init__(
            nS=_desc.size,
            nA=len(actions),
            P=transitions,
            isd=isd.flatten(),
        )

    def render(self, mode='human'):
        outfile = StringIO() if mode == 'ansi' else sys.stdout
        out = self.desc.copy().tolist()
        i, j = self.decode(self.s)

        out[i][j] = utils.colorize(out[i][j], 'blue', highlight=True)

        for row in out:
            print("".join(row))
        if self.lastaction is not None:
            print(
                f"({self.action_strings[self.lastaction]}) {self.decode(self.s)}\n"
            )
        else:
            print("\n")
        # No need to return anything for human
        if mode != 'human':
            return outfile
        out[i][j] = self.desc[i, j]

    def encode(self, i: int, j: int) -> int:
        nrow, ncol = self.desc.shape
        assert 0 <= i < nrow
        assert 0 <= j < ncol
        return int(i * ncol + j)

    def decode(self, s: int) -> Tuple[int, int]:
        nrow, ncol = self.desc.shape
        assert 0 <= s < nrow * ncol
        return int(s // ncol), int(s % ncol)

    def generate_matrices(self):
        self._transition_matrix = np.zeros((self.nS, self.nA, self.nS))
        self._reward_matrix = np.zeros((self.nS, self.nA, self.nS))
        for s1, action_P in self.P.items():
            for a, transitions in action_P.items():
                trans: Transition
                for trans in transitions:
                    self._transition_matrix[s1, a, trans.
                                            new_state] = trans.probability
                    self._reward_matrix[s1, a] = trans.reward
                    if trans.terminal:
                        for a in range(self.nA):
                            self._transition_matrix[trans.new_state, a, trans.
                                                    new_state] = 1
                            self._reward_matrix[trans.new_state, a] = 0
                            assert not np.any(self._transition_matrix > 1)

    @property
    def transition_matrix(self) -> np.ndarray:
        if self._transition_matrix is None:
            self.generate_matrices()
        return self._transition_matrix

    @property
    def reward_matrix(self) -> np.ndarray:
        if self._reward_matrix is None:
            self.generate_matrices()
        return self._reward_matrix


class GoalGridworld(Gridworld):
    def __init__(self, **kwargs):
        self.old_letter = None
        super().__init__(**kwargs)
        self.goal = None
        self.set_goal(self.observation_space.sample())
        self.goal_space = self.observation_space

    def set_goal(self, goal: int):
        if self.goal is not None:
            self.desc[tuple(self.decode(self.goal))] = self.old_letter
        idx = tuple(self.decode(goal))
        self.old_letter = self.desc[idx]
        self.desc[idx] = 'G'
        self.goal = goal

        self.P = {
            s: {
                a: [
                    t._replace(
                        reward=float(s == goal),
                        terminal=s == goal,
                    ) for t in transitions
                ]
                for a, transitions in Pa.items()
            }
            for s, Pa in self.P.items()
        }

        self._transition_matrix = None

    def sample_goal(self):
        return categorical_sample(self.isd, self.np_random)


if __name__ == '__main__':
    env = Gridworld(
        desc=['_t', '__'], rewards=dict(t=1), terminal=dict(t=True))
    env.reset()
    while True:
        env.render()
        time.sleep(1)
        env.step(env.action_space.sample())
