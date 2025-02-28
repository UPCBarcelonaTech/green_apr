# Appendix of paper: The Sustainability Face of Automated Program Repair Tools

## Summary

This repository has all data of the paper.
We have two types of files, located in two different folders:  [results/energy_summary/](results/energy_summary/) and [results/row_data/](results/row_data/)
1) Summary of the executions (traditional and LLM based APR). These files are located in [results/energy_summary/](results/energy_summary/).
Basically, each of these files summarises all the data (e.g., energy consumed, number of patches patches, correctness of patches, etc) from the executions of one APR tool on one particular bug
2) Row data generated by the experiments (APR logs, results, power measurements, etc). These files are located in [results/row_data/](results/row_data/)

These folders contains two subfolders: traditional-apr and llm_based, which contain the data from traditional APR (e.g., TBar, kPar, etc) and LLM based APR, respectively.


## Data for responding RQs


### RQ 1, 2, 3 

The RQ1, 2 and 3 are answered from the data provided in the summary files [results/energy_summary/](results/energy_summary/) and [results/row_data/](results/row_data/).
The correctness of patches (required to compute the answer from RQ2 and RQ3) is also included  the summary files [results/energy_summary/](results/energy_summary/). See [Patch assessment section](#patch-assessment) for detailed information.

### RQ 4

The RQ3 is answered from:
- The NPC metric that we computed, which is available at[results/row_data/metrics/npc](results/row_data/metrics/npc).
- Information about difficulty of fixing bugs obtained from ´Motwani, M., Sankaranarayanan, S., Just, R. et al. Do automated program repair techniques repair hard and important bugs?. Empir Software Eng 23, 2901–2947 (2018). https://doi.org/10.1007/s10664-017-9550-0´
The raw data is available at: https://github.com/LASER-UMASS/AutomatedRepairApplicabilityData/ 

These metrics (e.g., NCP, difficulty of repairing, etc) are studied together with the energy consumption.
The correlation between variables are available at: [results/row_data/metrics/values_correlation_LLMbased.json](results/row_data/metrics/values_correlation_LLMbased.json) and [results/row_data/metrics/values_correlation_traditionalAPR.json](results/row_data/metrics/values_correlation_traditionalAPR.json)


## Detailled explanation of data available in this appendix.

All the results of this experiments are obtained from the data disposed in folder [results/](results/)
The files from [results/energy_summary/](results/energy_summary/) contain the summary of the experiment for each Tool and Bug ID.
For example, the file [results/energy_summary/energy_summary_Avatar-Chart-1.json](results/energy_summary/energy_summary_Avatar-Chart-1.json) contains the energy consumption accross all the repair attemps of running the tool `Avatar` on  Defects4J bug with id `Chart 1`. 
That file also has the correctness assessment done on each patch.
The scripts for computing the Tables shown in that paper  are in the python file at [script/PaperResults.py](script/PaperResults.py) and read the summary files at [results/energy_summary/](results/energy_summary/).  

These sumary files are computed from the raws data available at [results/row_data/](results/row_data/)
In particular there are 3 subfolders:
- logs: contains the log of the repair attemps (e.g., a tool executed on a particular file). Example, file [results/row_data/traditional-apr/log/log_Avatar_Chart_1/log_out_Chart_1_Avatar.txt](results/row_data/traditional-apr/log/log_Avatar_Chart_1/log_out_Chart_1_Avatar.txt) contains the log of the *instrumented* version of Avatar tool for `Chart 1`. The log contains all the events (type of event + timestamp) that we register.

For example: the piece of log shown below display the event *[PF]*  patch found together with its timestamp *1659925031785*.
```
GPR[EPVATR]-1659925031773
19:17:11.773 [main] INFO edu.lu.uni.serval.avatar.AbstractFixer - Succeeded to fix the bug Chart_1====================
GPR[PF]-1659925031785

```

- metrics: contains the measure of the energy consumption of a repair attempt. Example, [results/row_data/metrics/metric_Avatar_Chart_1/cache_wattmetre_power_watt_job_metrics_Avatar-Chart-1.csv](results/row_data/metrics/metric_Avatar_Chart_1/cache_wattmetre_power_watt_job_metrics_Avatar-Chart-1.csv) contains the power consumption of Avatar tool during the repair attempt for bug Chart 1. 

Those files have two columns: timestamps and power. For example:
```
1662055748.421738,85.9
1662055748.441768,92.4
1662055748.461803,94.4
1662055748.481742,99.1
1662055748.501784,97.1
```
- patches: the patches found (if any). Example [results/row_data/patches/Avatar_Chart_1](results/row_data/patches/Avatar_Chart_1) contains the patches form Avatar that repair  bug Chart 1. All the patches have a timestamp in their names, so it's possible to sort the patches by generation time: it's the number that follows "\_ts\_",  for example:
```
Patch_6552628_1566_ts_1657139336721.txt
Patch_6565929_1567_ts_1657139350022.txt
Patch_6618328_1573_ts_1657139402421.txt
Patch_6644049_1575_ts_1657139428142.txt
Patch_6669955_1577_ts_1657139454048.txt
Patch_6695716_1579_ts_1657139479809.txt
Patch_6708462_1580_ts_1657139492555.txt
Patch_6749287_1586_ts_1657139533380.txt
```

In the case of LLM based APR

Due to the large scale of our experiment (many patches, large metric files), the size of all the row files is more than 100 Gb. Given the limit of the repository size from anonymous.4open.science, we pushed the files related to one repair attempts per tool-bug id (we recall that we execute at least  5 repair attempts per tool-bugid).
We will progressively update them, pushing all data to Zenodo.


 
## More documentations


#### Patch assessment
The labels of the patches are put in the summary files, in particular, under the array element called `Correctness_Per_Patch`: the i-th element of that array indicates the correctness of the i-th patch (chronologically sorted). A 'C' means *Correct*, other annotations such as 'I' or 'na' mean *incorrect*.
For example,  the summary of Avatar repairing Chart-1  [results/energy_summary/energy_summary_Avatar-Chart-1.json](results/energy_summary/energy_summary_Avatar-Chart-1.json)
indicates that the first patch [results/energy_summary/energy_summary_Avatar-Chart-1.json#L70](results/energy_summary/energy_summary_Avatar-Chart-1.json#L70) is correct. We recall that the patches from  [results/row_data/patches/Avatar_Chart_1](results/row_data/patches/Avatar_Chart_1) have the the time of generation in their file names.
We also recall that we do not analyze patch correctness beyond the first correct patch found (as in the paper we are only interested in the energy consumed to find the first correct patch).


#### Events
The explanation about events is in file  [doc/events.md](doc/events.md)



