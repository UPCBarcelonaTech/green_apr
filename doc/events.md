
# Logging Events during execution.

We store in the logs from a repair executions events occurred during the repair process. 
This log allows us to capture the time that each event (e.g., Fault localization, patch validation) starts and ends. 
Then using that information, we can calculate the energy consumption of each event.
For each event, we write the timestamp.
To log such events, we modify the source code of each repair tool in order to add the line that write the information.

##### Characteristics of an execution log: 

An example of log is: 

```
GPR[SFP]-1111111268083
GPR[SPS]-1111111268602
GPR[EPS]-1111111268623
GPR[SPS]-1111111268623
GPR[EPS]-1111111268634
GPR[SPVA]-1111111268634
GPR[SPVS]-1111111268634
GPR[SPVAP]-1111111268634
GPR[SPVS]-1111111270646
GPR[SPVAP]-1111111270646
GPR[SPVS]-1111111272987
GPR[SPVAP]-1111111272988
GPR[SPVS]-1111111275140
GPR[SPVAP]-1111111275140
GPR[SPVS]-1111111277109
GPR[SPVAP]-1111111277109
GPR[SPVESU]-1111111279525
GPR[EPVESU]-1111111279526
GPR[EPVA]-1111111279526
GPR[SPS]-1111111279526
GPR[EPS]-1111111279537
GPR[SPS]-1111111279537
GPR[EPS]-1111111279549
GPR[SPVA]-1111111279549
```

where `GPR` is just a prefix for all the events, [X]-Y corresponds to the ocurrence of event `X` at the timestamp `Y` (in milliseconds). 
In particular, it is represented as Epoch Unix Timestamp.
Events with prefix `S` remarks the start of one activity (e.g., patch validation), and `E` the end of that activity.

The list of events are:

* SSUP: start setup
* SFL: start fl (EFL (Note that before was FP due to an error))
* SFP: start fixing process, after FL is done.
* SPS: start patch systhesis/creation (creation of the patch from a template) (As we can have multiples patches)
* SPVA: validation of a set of patches (e.g., in TBar all patches from one template)
* SSUN: Start the analysis of one suspicious
* SPVS: validation of single patch 
* SPVAP: Apply and configure patch
* SPVATF: test running failing
* SPVATR: test running regression
* SPVESU: Environment setup, cleaning files after validation

The events that start with an `e` instead of a `s` represents the end of a event.

Other events neither have `e` nor `s`. Such as `PF: Patch found`, which indicates the moment a patch is found.


Also related with the sleeps (which aims to stabilize the energy consumption)

* SSLI: before the sleep of one minute executed just the job is launched
* SSLB: before the sleep of one minute executed  after D4j setup and before calling the tool
* SSLE: before the sleep of one minute executed at the end of the script


# 
