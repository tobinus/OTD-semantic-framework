#precision(res, set_map, OTD.Location)

def confusion_matrix_scores(result_set, reference_set, complete_set):
    fp, fn, tp, tn = [0 for _ in range(4)]    
    for d in complete_set:
        if (d in result_set) and (d in reference_set):
            tp += 1
        elif (d in result_set) and (d not in reference_set):
            fp += 1
        elif (d not in result_set) and (d in reference_set):
            fn += 1
        elif (d not in result_set) and (d not in reference_set):
            tn += 1
    class csm: pass
    csm.fp = fp
    csm.fn = fn
    csm.tp = tp
    csm.tn = tn
#    print ("confusion matrix: ", csm.fp, csm.fn, csm.tp, csm.tn)
    return csm

def precision(cms):
    if (cms.tp + cms.fp) > 0:
        return cms.tp / (cms.tp + cms.fp)
    return 0

def recall(cms):
    if (cms.tp + cms.fn) > 0:
        return cms.tp / (cms.tp + cms.fn)
    return 0

def true_negative_rate(cms):
    if (cms.tn + cms.fp) > 0:    
        return cms.tn / (cms.tn + cms.fp)
    return 0

def accuracy(cms):
    if (cms.tp + cms.tn + cms.fp + cms.fn) > 0:    
        return (cms.tp + cms.tn) / (cms.tp + cms.tn + cms.fp + cms.fn)
    return 0

def f1_score(cms):
    if (cms.tp+cms.fp+cms.fn) > 0:
        return (2*cms.tp)/(2*cms.tp+cms.fp+cms.fn)
