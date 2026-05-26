 # necessary methods can be imported from here

import os
import glob
from collections import defaultdict

def print_status(msg,kind='short',line=None):
	
	if line is None:
		line=len(msg)

	if kind=='short':
		print('++ '+msg)
	else:
		print('++ '+line*'-')
		print('++ '+msg)
		print('++ '+line*'-') 


def print_shape(a,var_name=None):
	if var_name is None:
		var_name='given variable'

	print_status('Shape of '+ var_name + ' is '+ str(a.shape))


def elapsed_time_string(st,et,round_by=3): 
	""" 
	returns elapsed time between start (st) and end (et) time in provided in sec 

	"""
	
	elapsed_time=et-st  
	
	if int(elapsed_time//60)==0:
		msg=str(round(elapsed_time,round_by)) + ' s'
	elif int(elapsed_time//3600)==0:
		msg=str(round(elapsed_time/60,round_by)) + ' min(s)'
	elif int(elapsed_time//(3600*24))==0:
		msg=str(round(elapsed_time/3600,round_by)) + ' hour(s)'
	elif int(elapsed_time//(3600*24*7))==0:
		msg=str(round(elapsed_time/(3600*24),round_by)) + ' day(s)'
	else:
		msg=str(round(elapsed_time/(3600*24*7),round_by)) + ' week(s)'
	return  msg  # Adding a white space before the message 


def print_timings(rank,log_dict):
    print("------------------------------------------------------------------------") 
    print(f"                     Timing Summary for Rank {rank}                     ")
    print("------------------------------------------------------------------------") 
    
    keys = list(log_dict.keys())
    
    if keys:   # If at least one key exists
        for i in range(1, len(keys)):
            elapsed_time = elapsed_time_string(log_dict[keys[i - 1]],log_dict[keys[i]])
            #print(elapsed_time)
            #duration = timing_log[keys[i]] - timing_log[keys[i - 1]]
            print(f"[From Rank {rank}] {keys[i - 1]} ==>  {keys[i]} took " + elapsed_time)
        
    else:
        print("++  No timings have been marked so far!!! Please use mark_time() method...NOT OK!!!")
    print("------------------------------------------------------------------------\n\n")
      
  
def make_synapse_dict(synapse,index_target=1):
    res = defaultdict(list)
    for tup in synapse:
        res[tup[index_target]].append(tup)    # index of the target gid in the synapse table    
    return res   
  
def silently_remove_files(directory, *patterns):
    for pattern in patterns:
        for filepath in glob.glob(os.path.join(directory, pattern)):
            try:
                #print('Silently deleting unnecessary database files')
                os.unlink(filepath)
            except (OSError, IOError):
                pass 
             
def remove_overlapping_gids(syn):
    result = []
    previous_set = set()
    for lst in syn:
        # Remove elements already present in previous lists
        result_list = [x for x in lst if x not in previous_set]
        result.append(result_list)
        # Update the set of "forbidden" elements for the next list
        previous_set.update(lst) 
    return result
            
            
def equalize_sublists(lsts):
    flat = []
    for sublist in lsts:
        flat.extend(sublist)
        
    n = len(lsts)
    total = len(flat)
    quotient, remainder = divmod(total, n)
    sizes = [quotient + 1 if i < remainder else quotient for i in range(n)]
    result = []
    start = 0
    
    for size in sizes:
        result.append(flat[start:start+size])
        start += size
        
    return result  