#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import math

from abmtemplate.basemodel import BaseModel

from config import Config
from agent import Agent


class Model(BaseModel):
    identifier = ""
    model_parameters = {}
    agents = []
    interactions = None

    def __init__(self, model_config):
        super(Model, self).__init__(model_config)

    def get_identifier(self):
        return self.identifier
    def set_identifier(self, _value):
        super(Model, self).set_identifier(_value)

    def get_model_parameters(self):
        return self.model_parameters
    def set_model_parameters(self, _value):
        super(Model, self).set_model_parameters(_value)

    def get_agents(self):
        return self.agents
    def set_agents(self, _value):
        super(Model, self).set_agents(_value)

    def get_interactions(self):
        return self.interactions
    def set_interactions(self, _value):
        super(Model, self).set_interactions(_value)

    def __str__(self):
        return super(Model, self).__str__()


    def initialize_agents(self):
        num_agents = int(self.model_parameters['num_agents'])

        # construct agent_parameters dict
        agent_parameters = {'rho': float(self.model_parameters['rho'])}

        # TODO: these values should be set in the model config file somehow, so this code has to be refactored
        d1_lower = 0.1
        d1_upper = min(self.model_parameters['RG']/(self.model_parameters['lambda']+self.model_parameters['eta']), 1.5)
        y_lower = 0.0
        y_upper = 1.0
        b_lower = 0.0
        b_upper = min(self.model_parameters['eta']*d1_upper, y_upper)
        state_variables = {'d1': [d1_lower, d1_upper], 'y': [y_lower, y_upper], 'b': [b_lower, b_upper]}

        # create agents and append them to the array of agents
        for i in range(0, num_agents):
            identifier = str(i)
            _agent = Agent(identifier, agent_parameters, state_variables)
            self.agents.append(_agent)

    # TODO this code is fairly generalized, refactor it and move it into BaseAgent class
    def get_agent_by_id(self, _id):
        for agent_iterator in self.agents:
            if agent_iterator.identifier == _id:
                return agent_iterator

    # TODO this code is fairly generalized, refactor it and move it into BaseAgent class
    def check_agent_homogeneity(self):
        for parameter_iterator in self.agents[0].parameters:
            temp_parameter = self.agents[0].parameters[parameter_iterator]
            for agent_iterator in self.agents:
                if agent_iterator.parameters[parameter_iterator] != temp_parameter:
                    return False
                temp_parameter = agent_iterator.parameters[parameter_iterator]
        for parameter_iterator in self.agents[0].state_variables:
            temp_state_variable = self.agents[0].state_variables[parameter_iterator]
            for agent_iterator in self.agents:
                if agent_iterator.state_variables[parameter_iterator] != temp_state_variable:
                    return False
                temp_state_variable == agent_iterator.state_variables[parameter_iterator]
        return True


    # -----------------------------------------------------------------------
    #
    # expected utilities
    #
    # -----------------------------------------------------------------------
    def expected_utility_A(self, agent):
        lamb = self.get_model_parameters()['lambda']
        value = agent.u1_A*(lamb + (1-lamb)*agent.theta_A) + (1-lamb)*(1-agent.theta_A)*0.5*(agent.u2_AG + agent.u1_A)
        if (agent.theta_A > 0.5):
            value = -nan
        return value

    def expected_utility_CE(self, agent):
        value = q_H*(  theta_CE*state.u_dc + (1-theta_CE)*( lamb*state.u_d_1 + (1-lamb)*0.5*(state.u2_Gce + state.u_d_ce) )  )
        value += (1-q_H)*(lamb*state.u_d_1 + (1-lamb)*0.5*(state.u2_Gce + state.u2_Bce))
        if (theta_CE > 0.5):
            value = -nan
        return value

    def expected_utility_H(self, agent):
        q_H = self.get_model_parameters()['q']
        lambda_H = self.get_model_parameters()['lambda'] + self.get_model_parameters()['eta']
        theta_H_bar = agent.theta_H  # the bar nomenclature is outdated, but i don't want to change all the code

        value = (1.0-q_H)*(lambda_H*agent.u_d_1 + (1.0-lambda_H)*0.5*(agent.u_HG+agent.u_HB))
        value += q_H*(theta_H_bar*agent.u_d_H + lambda_H*(1.0-theta_H_bar)*agent.u_d_1)
        value += q_H*(1.0-theta_H_bar)*(1-lambda_H)*0.5*(agent.u_HG + agent.u_d_H)
        if (theta_H_bar > 0.5):
            value = -nan
        return value

    # cr
    def expected_utility_1L(self, agent):
        # set of local parameters needed to make the computation of the value a bit less cumbersome
        q_H = self.get_model_parameters()['q']
        q_L = q_H
        lambda_L = self.get_model_parameters()['lambda'] - self.get_model_parameters()['eta']
        theta_H_bar = agent.theta_H
        theta_1L_bar = agent.theta_L
        a_H = q_H*theta_H_bar

        value = (1.0-q_L)*(  lambda_L*agent.u_d_1 + (1.0-lambda_L)*0.5*( (1.0-a_H)*(agent.u_LGN + agent.u_LBN) + a_H*(agent.u_LGD + agent.u_LGN) )  )
        value += q_L*( theta_1L_bar*((1.0-a_H)*agent.u_d_LN + a_H*agent.u_d_LD) + lambda_L*(1-theta_1L_bar)*agent.u_d_1 )
        value += q_L*(1.0-lambda_L)*0.5*( (1.0-theta_1L_bar*theta_1L_bar)*((1.0-a_H)*agent.u_LGN + a_H*agent.u_LGD) +
                                        (1.0-theta_1L_bar)*(1.0-theta_1L_bar)*((1.0-a_H)*agent.u_LBN + a_H*agent.u_LBD) )
        if ( (theta_1L_bar > 0.5) ):
            value = -nan
        return value

    # cr + ic
    def expected_utility_2L(self, agent):
        # set of local parameters needed to make the computation of the value a bit less cumbersome
        q_H = self.get_model_parameters()['q']
        q_L = q_H
        lambda_L = self.get_model_parameters()['lambda'] - self.get_model_parameters()['eta']
        theta_H_bar = agent.theta_H
        theta_2LN_bar = agent.theta_LN
        theta_2LD_bar = agent.theta_LD
        a_H = q_H*theta_H_bar

        value = (1.0-q_L)*(  lambda_L*agent.u_d_1 + (1.0-lambda_L)*0.5*((1.0-a_H)*(agent.u_LGN+agent.u_LBN)
                                                                        + a_H*(agent.u_LGD+agent.u_LBD))  )
        value += q_L*(  theta_2LN_bar*(1.0-a_H)*agent.u_d_LN + theta_2LD_bar*a_H*agent.u_d_LD
                        + lambda_L*(a_H*(1.0-theta_2LD_bar) + (1.0-a_H)*(1-theta_2LN_bar))*agent.u_d_1 )
        value += q_L*(  (1.0-lambda_L)*0.5*( (1.0-a_H)*((1.0-theta_2LN_bar*theta_2LN_bar)*agent.u_LGN
                                                        + (1.0-theta_2LN_bar)*(1.0-theta_2LN_bar)*agent.u_LBN)
                                             + a_H*((1.0-theta_2LD_bar*theta_2LD_bar)*agent.u_LGD
                                                    + (1-theta_2LD_bar)*(1-theta_2LD_bar)*agent.u_LBD) )  )
        if ( (theta_2LN_bar > 0.5) or (theta_2LD_bar > 0.5) ):
            value = -nan
        return value

    # ce
    def expected_utility_5(self, agent):
        # set of local parameters needed to make the computation of the value a bit less cumbersome
        q_H = self.get_model_parameters()['q']
        q_L = q_H
        lamb = self.get_model_parameters()['lambda']
        theta_bar = agent.theta

        value = 0.5*(q_H + q_L)*(  theta_bar*agent.u_dc + (1.0-theta_bar)*(lamb*agent.u_d_1
                                                                           + (1.0-lamb)*0.5*(agent.u_Gc + agent.u_dc) )  )
        value += 0.5*(1.0-q_H + 1.0-q_L)*( lamb*agent.u_d_1 + (1.0-lamb)*0.5*(agent.u_Gc + agent.u_Bc) )
        if (theta_bar > 0.5):
            value = -nan
        return value

    # ce + ic
    def expected_utility_6(self, agent):
        # set of local parameters needed to make the computation of the value a bit less cumbersome
        q_H = self.get_model_parameters()['q']
        q_L = q_H
        lamb = self.get_model_parameters()['lambda']
        theta_bar = agent.theta

        value = (q_H + q_L - q_H*q_L)*(  theta_bar*agent.u_dc
                                         + (1.0-theta_bar)*(lamb*agent.u_d_1 + 0.5*(1.0-lamb)*(agent.u_Gc + agent.u_dc) )  )
        value += (1.0-q_H)*(1.0-q_L)*( lamb*agent.u_d_1 + (1.0-lamb)*0.5*(agent.u_Gc + agent.u_Bc) )

        if (theta_bar > 0.5):
            value = -nan

        return value

    # -----------------------------------------------------------------------

    def calculate_EUA(self, agent):
        EUA = self.expected_utility_A(agent)
        return EUA

    def calculate_EUCE(self, agent):
        EUCE = self.expected_utility_CE(agent)
        return EUCE

    def calculate_EU1(self, agent):
        EU1_H = self.expected_utility_H(agent)
        EU1_L = self.expected_utility_1L(agent)
        EU1 = 0.5*(EU1_H + EU1_L)
        return EU1

    def calculate_EU2(self, agent):
        theta_2LN_bar = agent.theta_LN
        theta_2LD_bar = agent.theta_LD
        if (theta_2LN_bar > theta_2LD_bar):
            EU2 = -nan
        else:
            EU_H = self.expected_utility_H(agent)
            EU2_L = self.expected_utility_2L(agent)
            EU2 = 0.5*(EU_H + EU2_L)
        return EU2


    def calculate_EU5(self, agent):
        return self.expected_utility_5(agent)

    def calculate_EU6(self, agent):
        return self.expected_utility_6(agent)




    # -----------------------------------------------------------------------
    #
    # compute optimum
    #
    # -----------------------------------------------------------------------
    def find_optimum(self, agent):
        global nan
        nan = 10000000000000000.0

        d1 = agent.state_variables['d1']
        d1_lower = float(d1[0])
        d1_upper = float(d1[1])
        step_d1 = (d1_upper - d1_lower)/self.steps_per_state_variable

        y = agent.state_variables['y']
        y_lower = float(y[0])
        y_upper = float(y[1])
        step_y = (y_upper - y_lower)/self.steps_per_state_variable

        b = agent.state_variables['b']
        b_lower = float(b[0])
        b_upper = float(b[1])
        step_b = (b_upper - b_lower)/self.steps_per_state_variable

        maxA = [-nan, d1_lower, y_lower, b_lower]
        max1 = [-nan, d1_lower, y_lower, b_lower]
        max2 = [-nan, d1_lower, y_lower, b_lower]
        max5 = [-nan, d1_lower, y_lower, b_lower]
        max6 = [-nan, d1_lower, y_lower, b_lower]

        d1 = d1_lower
        while d1 <= d1_upper:
            y = y_lower
            while y <= y_upper:
                b = b_lower
                while b <= b_upper:
                    # first set agentA state variables
                    agent.set_state_variables({'d1': d1, 'y': y, 'b': b})
                    agent.compute_ancillary_variables(self.model_parameters['R'],
                                                      self.model_parameters['beta'],
                                                      self.model_parameters['lambda'],
                                                      self.model_parameters['phi'],
                                                      self.model_parameters['eta'])

                    # - we have to compute 4 different cases: cr, cr+ic, ce, ce+ic, and evaluate cr+ic and ce+ic at
                    #   their optimal contract as well as at the contract of cr and ce, respectively.
                    # - it is more efficient to compute all six expected utilities at once and store the optimum of
                    #   the state variables in an array of optimum variables

                    EUA = self.calculate_EUA(agent)
                    if (EUA > maxA[0]):
                        maxA = [EUA, d1, y, b]

                    EU1 = self.calculate_EU1(agent)
                    if (EU1 > max1[0]):
                        max1 = [EU1, d1, y, b]

                    EU2 = self.calculate_EU2(agent)
                    if (EU2 > max2[0]):
                        max2 = [EU2, d1, y, b]

                    EU5 = self.calculate_EU5(agent)
                    if (EU5 > max5[0]):
                        max5 = [EU5, d1, y, b]

                    EU6 = self.calculate_EU6(agent)
                    if (EU6 > max6[0]):
                        max6 = [EU6, d1, y, b]

                    # increase b
                    b += step_b
                # increase y
                y += step_y
            # increase d1
            d1 += step_d1
        print max1, max2, max5, max6


    # TODO this code is fairly general and should be generalized further and then moved to the BaseAgent class
    def compute_equilibrium_recursive(self, agentA, agentB):
        self.par_keys = []
        self.par_lower = []
        self.par_upper = []
        self.par_step  = []
        self.par_current = []
        for state_key, state_var in agentA.state_variables:
            self.par_keys.append(str(state_key))
            self.par_lower.append(float(state_var[0]))
            self.par_upper.append(float(state_var[1]))
            self.par_step.append((self.par_upper[-1] - self.par_lower[-1]) / self.steps_per_state_variable)

        self.precision = 0.01
        self.par_current = self.par_lower
        self.loop_over_dimension(0, agentA, agentB)

    # TODO this code is fairly general and should be generalized further and then moved to the BaseAgent class
    def loop_over_dimension(self, recursion_level, agentA, agentB):
        while self.par_current[recursion_level] <= self.par_upper[recursion_level]:
            if (recursion_level+1) < len(self.par_upper):
                self.par_current[recursion_level+1] = self.par_lower[recursion_level+1]
                self.loop_over_dimension(recursion_level+1, agentA, agentB)
            elif (recursion_level+1) == len(self.par_upper):
                # first set agentA state variables
                for state_iterator in range(0,len(self.par_keys)):
                    agentA.state_variables[self.par_keys[state_iterator]] = self.par_current[state_iterator]

                # then get the best response of B given the current portfolio choice of A
                ret_B = agentB.get_best_response(self.par_current)

                # and then get the best response of A given the best response of B
                ret_A = agentA.get_best_response(ret_B)

                # check if we have a fixed point
                if all(i < self.precision for i in [abs(x) - y for x, y in zip(ret_A, self.par_current)])
                    # here we have to write out the results
                    pass
            self.par_current[recursion_level] += self.par_step[recursion_level]


    # =======================================================================
    # do_update
    # =======================================================================
    def do_update(self):
        # equilibrium is symmetric, i.e. we only require one agent
        agent = self.agents[0]

        self.steps_per_state_variable = int(round(math.pow(float(self.model_parameters['num_sweeps']),
                                                           1.0/len(agent.state_variables)), 0))

        self.find_optimum(agent)
