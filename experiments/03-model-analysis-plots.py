# %% Imports
import os

from pacsltk.pacs_util import *
from pacsltk import perfmodel

import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters

import matplotlib.pyplot as plt

from pacswg.timer import *

from tqdm.auto import tqdm

tqdm.pandas()
register_matplotlib_converters()

# %% Make Plots
figs_folder = "figs"


def get_fig_path(x): return (os.path.join(figs_folder, "exp" +
                                          x + ".png"), os.path.join(figs_folder, "exp" + x + ".pdf"))


def tmp_fig_save(fig_name):
    paths = get_fig_path(fig_name)
    plt.savefig(paths[0], dpi=300)
    plt.savefig(paths[1])


prepare_matplotlib_cycler()


# %% Perform Tractability Analysis
idle_mins_before_kill = 10


def analyze_sls(row):
    timer = TimerClass()
    timer.tic()
    props, _ = perfmodel.get_sls_warm_count_dist(**row)
    t = timer.toc()
    props['ProcessingTime'] = t
    return pd.Series(props)

workloads = [
    (2.0, 2.2, "W1"), (0.3, 10, "W2"), (0.02, 1, "W3"), (4.211, 5.961, "W4"), (1.809, 26.681, "W5")
]

dfs = []
for warm_service_time, cold_service_time, _ in workloads:
    params = {
        "arrival_rate": 1,
        "warm_service_time": warm_service_time,
        "cold_service_time": cold_service_time,
        "idle_time_before_kill": np.append(np.arange(.1, 10, .1), np.arange(10, 10*60, 10)),
    }
    df = pd.DataFrame(data=params)
    df = pd.concat([df, df.progress_apply(analyze_sls, axis=1)], axis=1)
    dfs.append(df)

    
# %% Plot the What-Ifs
from matplotlib.ticker import ScalarFormatter

def plot_configs(ylab, is_texp=True):
    plt.legend()
    plt.tight_layout()
    plt.grid(True)
    plt.xlabel("Expiration Threshold (s)")
    plt.ylabel(ylab)
    plt.gcf().subplots_adjust(left=0.15, bottom=0.22)
    if is_texp:
        plt.xticks(list(plt.xticks()[0]) + [600])
        plt.xlim((0.1*0.9,600*1.1))
    plt.gca().xaxis.set_major_formatter(ScalarFormatter())


# Utilization
plt.figure(figsize=(4, 3))
idx = 0
for df in dfs:
    warm_service_time, cold_service_time, label = workloads[idx]
    plt.semilogx(df['idle_time_before_kill'], df['avg_utilization'] *
                 100, label=label)
    idx += 1

plot_configs("Utilization (%)")
tmp_fig_save("08_variable_texp_util")

# Cold Start Probability
plt.figure(figsize=(4,2))
idx = 0
for df in dfs:
    warm_service_time, cold_service_time, label = workloads[idx]
    plt.semilogx(df['idle_time_before_kill'], df['cold_prob'] *
                 100, label=label)
    idx += 1

plot_configs("Prob. of Cold Start (%)")
tmp_fig_save("08_variable_texp_pcold")


# Average Response Time
plt.figure(figsize=(4,3))
idx = 0
colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728','#9467bd', '#8c564b', '#e377c2', '#7f7f7f','#bcbd22', '#17becf']
exp_thresholds = []
for df in dfs:
    exp_thresholds.append(df.loc[df['avg_resp_time'] < df['warm_service_time'][0] * \
         1.3, 'idle_time_before_kill'].min())

for df in dfs:
    warm_service_time, cold_service_time, label = workloads[idx]
    plt.semilogx(df['idle_time_before_kill'], df['avg_resp_time'] *
                 1, linestyle='-', label=label)
    plt.axvline(exp_thresholds[idx], color=colors[idx], linestyle='--')
    plt.plot(exp_thresholds[idx], min(warm_service_time*1.3, df['avg_resp_time'].max()), 'd', color=colors[idx])
    idx += 1

plt.ylim((0,10))

plot_configs("Avg. Response Time (s)")

tmp_fig_save("08_variable_texp_rt_avg")


# Num of Instances in Warm Pool
plt.figure(figsize=(4,2))
idx = 0
for df in dfs:
    warm_service_time, cold_service_time, label = workloads[idx]
    plt.semilogx(df['idle_time_before_kill'], df['avg_server_count'], label=label)
    idx += 1

plot_configs("Average Instance Count")
tmp_fig_save("08_variable_texp_inst_count")

# User Cost Estimate
plt.figure(figsize=(4,3))
idx = 0
for df in dfs:
    warm_service_time, cold_service_time, label = workloads[idx]
    cost_estimate = df['avg_server_count_total'] * df['avg_resp_time']
    cost_estimate = cost_estimate / cost_estimate.max()
    plt.loglog(df['idle_time_before_kill'], cost_estimate, label=label)
    plt.gca().yaxis.set_major_formatter(ScalarFormatter())
    idx += 1

plot_configs("Normalized Estimated User Cost")
tmp_fig_save("08_variable_texp_user_cost_estimate")

# %% Rejection Probability Calculations
dfs = []
for warm_service_time, cold_service_time, _ in workloads:
    params = {
        "arrival_rate": np.logspace(2, 5, num=100),
        "warm_service_time": warm_service_time,
        "cold_service_time": cold_service_time,
        "idle_time_before_kill": 600,
    }
    df = pd.DataFrame(data=params)
    df = pd.concat([df, df.progress_apply(analyze_sls, axis=1)], axis=1)
    dfs.append(df)
#%% Rejection Probability Plot

plt.figure(figsize=(4,2))
idx = 0
for df in dfs:
    warm_service_time, cold_service_time, label = workloads[idx]
    plt.semilogx(df['arrival_rate'], df['rejection_prob'], label=label)
    idx += 1

plot_configs("Prob. of Rejection", is_texp=False)
plt.xlabel('Arrival Rate (reqs/s)')
tmp_fig_save("09_variable_texp_prob_reject")
