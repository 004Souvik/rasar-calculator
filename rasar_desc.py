import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.ML.Descriptors import MoleculeDescriptors



def similarity_calculator(df1: pd.DataFrame, df2: pd.DataFrame, method="Gaussian Kernel"):
    """
    This function calculates the pairwise-similarity between two dataframes based on their descriptor matrix. \n
    df1: descriptor matrix for the training set \n
    df2: descriptor matrix for the test set \n
    method: Gaussian Kernel (at sigma = 1) or Laplacian Kernel (at gamma = 1) \n
    return: pairwise-similarity values
    """
    similarity = []
    for i in range(len(df2)):
        temp = []
        for j in range(len(df1)):
            if method == "Gaussian Kernel":
                sim = np.exp(-sum((df2.values[i] - df1.values[j])**2)/2)
            if method == "Laplacian Kernel":
                sim = np.exp(-sum(np.abs(df2.values[i] - df1.values[j])))
            temp.append(sim)
        similarity.append(temp)
    similarity_df = pd.DataFrame(similarity, index=df2.index, columns=df1.index.tolist())
    return similarity_df

#scaling
def standerdization(df1: pd.DataFrame, df2: pd.DataFrame):
    avg=df1.mean()
    stdv=df1.std()
    ndf1=(df1-avg)/stdv
    ndf2=(df2-avg)/stdv
    return ndf1, ndf2


#sorting function
def data_sort(frame: pd.DataFrame, id):#id is the index of the new data frame
    df_sorted = pd.DataFrame(frame.apply(lambda row: sorted(zip(frame.columns, row), 
                                                            key=lambda x: x[1], reverse=True), axis=1).tolist(), index=id)
    df_val = pd.DataFrame(frame.apply(lambda row: [x[1] for x in sorted(zip(frame.columns, row), 
                                                                        key=lambda x: x[1], reverse=True)], 
                                                                        axis=1).tolist(), index=id)
    df_sorted_columns = pd.DataFrame(frame.apply(lambda row: [x[0] for x in sorted(zip(frame.columns, row), 
                                                                                   key=lambda x: x[1], reverse=True)], 
                                                                                   axis=1).tolist(), index=id)
    
    return df_sorted, df_val, df_sorted_columns




def rasar(df3: pd.DataFrame, df4: pd.DataFrame, method="Gaussian Kernel"):
    """
    
    This function is used for the rasar descriptor calculation \n
    df3: Training set or source compound sets (contains both descriptors and response values) \n
    first coulmn should be id column [Id-descriptor-Response] \n
    df4: Test set or target set (descriptors with similar arrangements as in df3) \n
    Response may not be present (if present, not affect the prediction) \n
    first column also should be id column [Id-descriptor-Response (if present)] \n
    method: By deafult method is set to Gaussian Kernel, but it can be changed to Laplacian Kernel \n
    return: rasar descriptors
    ========================================================================================
    CTC (close training compound) is set at less than equal to 10. \n
    For training set: df3 and df4 both are train set (same compounds are ignored during calculation). \n
    For test set: df3 is training set and df4 is test set.
    """
    xtr = df3.iloc[:,:-1]
    ytr = df3.iloc[:,-1]
    if len(df4.columns) == len(df3.columns):
        xte = df4.iloc[:,:-1]
    else:
        xte = df4

    std_xtr, std_xte = standerdization(df1=xtr, df2=xte)
    sim = similarity_calculator(df1=std_xtr, df2=std_xte, method=method)
    if np.array_equal(sim.index.values, sim.columns.values):
        np.fill_diagonal(sim.values, 0)
    else:
        pass
    sim1 = sim.copy()
    sim1.columns = ytr.values.tolist()
    df_sort_res, sort_val_res, sort_col_res = data_sort(sim1, id=df4.index)
    similarity_sum = sort_val_res.sum(axis=1)
    if len(xtr) >= 10:
        ctc=10
    else:
        ctc=len(xtr)
    sort_val_res1=sort_val_res.iloc[:,0:ctc]
    sort_col_res1=sort_col_res.iloc[:,0:ctc]
    wei1 = (sort_val_res1.T/similarity_sum).T
    wei_res1 = wei1*sort_col_res1
    wap=wei_res1.sum(axis=1)/wei1.sum(axis=1)

    
    #n_effective
    weitage2 = wei1**2
    n_eff = ((wei1.sum(axis=1))**2)/(weitage2.sum(axis=1))

    #sd_activity
    tem_nu = wei1*((sort_col_res1.sub(wap, axis=0))**2)
    tem_nu_sum = tem_nu.sum(axis=1)
    sda_part1 = (tem_nu_sum)/(wei1.sum(axis=1))
    sda_part2 = n_eff/(n_eff-1)
    sd_activity = pd.Series(np.sqrt(sda_part1*sda_part2))

    #cv_activity
    cv_activity = sd_activity.div(wap)

    #avg_similarity
    avg_similarity = sort_val_res1.mean(axis=1)

    #sd_similarity
    sd_similarity = sort_val_res1.std(axis=1)

    #cv_similarity
    cv_similarity = sd_similarity/avg_similarity

    #standard_error
    stand_error = sd_activity.div(np.sqrt(n_eff))

    #max_pos & maxpos_avgsim
    mp_res = sort_col_res1.copy()
    mp_res[mp_res<float(ytr.mean())] = np.nan
    mp_sim = sort_val_res1.where(~mp_res.isna(), np.nan)
    max_pos = mp_sim.max(axis=1)
    max_pos.fillna(0, inplace=True)
    maxpos_avgsim = mp_sim.mean(axis=1)
    maxpos_avgsim.fillna(0, inplace=True)

    #max_neg & maxneg_avgsim
    ne_res = sort_col_res1.copy()
    ne_res[ne_res>=float(ytr.mean())] = np.nan
    ne_sim = sort_val_res1.where(~ne_res.isna(), np.nan)
    max_neg = ne_sim.max(axis=1)
    max_neg.fillna(0, inplace=True)
    maxneg_avgsim = ne_sim.mean(axis=1)
    maxneg_avgsim.fillna(0, inplace=True)

    #abs_diff
    abs_diff = np.abs(max_pos-max_neg)

    #g and gm
    pos_frac = mp_sim.count(axis=1)/sort_col_res1.count(axis=1)
    pos_frac_diff = 2*np.abs(pos_frac-0.5)
    gm_val = np.where(max_pos >= max_neg, pos_frac_diff, -pos_frac_diff)

    #derived metrics
    gm_avgsim = gm_val*avg_similarity
    gm_sdsim = gm_val*sd_similarity

    #sm1 and sm2
    sm1 = (max_pos-max_neg)/np.maximum(max_pos, max_neg)
    sm2 = (maxpos_avgsim -maxneg_avgsim)/avg_similarity

    met_dict = {
        "RA_function": wap,
        "SD_Activity": sd_activity,
        "CV_Activity": cv_activity,
        "Avg_similarity": avg_similarity,
        "SD_similarity": sd_similarity,
        "CV_similarity": cv_similarity,
        "Standard_Error (SE)": stand_error,
        "MaxPos": max_pos,
        "PosAvgSim": maxpos_avgsim,
        "MaxNeg": max_neg,
        "NegAvgSim": maxneg_avgsim,
        "AbsDiff": abs_diff,
        "gm": gm_val,
        "gm*AvgSim": gm_avgsim,
        "gm*SD_Similarity": gm_sdsim,
        "sm1": sm1,
        "sm2": sm2
    }
    if ytr.sum() == ytr.value_counts().get(1,0):
        remove_itm = {"SD_Activity", "CV_Activity", "Standard_Error (SE)"}
        met_dict = {k: v for k, v in met_dict.items() if k not in remove_itm}
    else:
        met_dict = met_dict
    return met_dict
    

def rasar_desc_calculation(df5: pd.DataFrame, df6: pd.DataFrame, des, method="Gaussian Kernel"):
    """
    for RDKit descriptor calculation, df5 and df6 should contains SMILES [Id-SMILES-Response]
    """
    def rdkit_des(smiles_list):
        selected_descriptors = ["MolWt", "NumHDonors", "NumHAcceptors", "MolLogP", "TPSA", 
                                "NumRotatableBonds", "BalabanJ", "RingCount", "NumAliphaticRings", 
                                "NumAromaticRings", "FractionCSP3", "HeavyAtomCount"]
        calculator = MoleculeDescriptors.MolecularDescriptorCalculator(selected_descriptors)

        data = []
        for smiles in smiles_list:
            mol = Chem.MolFromSmiles(smiles)
            desc_values = calculator.CalcDescriptors(mol)
            data.append(desc_values)
        df = pd.DataFrame(data, columns=selected_descriptors)
        return df
    def all_rdkit_des(smiles_list):
        def get_all_descriptors(mol):
            results = {}
            for name, func in Descriptors._descList:
                try:
                    results[name] = func(mol)
                except:
                    results[name] = None  
            return results
        data1 = []
        for smi in smiles_list:
            mol = Chem.MolFromSmiles(smi)
            all_desc = get_all_descriptors(mol)
            data1.append(all_desc)
        all_desc_df = pd.DataFrame(data1)
        return all_desc_df

    if des =="User Defined Descriptors":
        rasar_descriptors = rasar(df3=df5, df4=df6, method=method)
    else:
        tr_smiles = df5.iloc[:,0]
        te_smiles = df6.iloc[:,0]
        if des =="Selected RDKit Descriptors":
            tr_rdkit_desc = rdkit_des(tr_smiles)
            te_rdkit_desc = rdkit_des(te_smiles)
        elif des == "All RDKit Descriptors":
            tr_rdkit_desc = all_rdkit_des(tr_smiles)
            te_rdkit_desc = all_rdkit_des(te_smiles)
        tr_rdkit_desc.index = df5.index
        te_rdkit_desc.index = df6.index
        #removal of the descriptors
        variance = tr_rdkit_desc.var()
        descriptors_to_remove = variance[variance <= 0.1].index.tolist()
        tr_rdkit_desc = tr_rdkit_desc.drop(columns=descriptors_to_remove)
        te_rdkit_desc = te_rdkit_desc.drop(columns=descriptors_to_remove)
        tr_rdkit_desc["Response"] = df5.iloc[:, 1]
        rasar_descriptors = rasar(df3=tr_rdkit_desc, df4=te_rdkit_desc, method=method)
    return rasar_descriptors

