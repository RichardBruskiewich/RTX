import pandas as pd
import numpy as np
import scipy as sci
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import sklearn as skl
import sklearn.linear_model as lm
import sklearn.externals as ex
import sklearn.ensemble as ensemble
import sklearn.metrics as met
import sklearn.model_selection as ms
import time
import argparse
import ast
from sklearn.externals import joblib
import random
import itertools



parser = argparse.ArgumentParser()
parser.add_argument("--tp", type=str, nargs='*', help="The filenames or paths to the true positive csvs", default=['semmed_tp.csv','mychem_tp.csv','mychem_tp_umls.csv','NDF_TP.csv'])
parser.add_argument("--tn", type=str, nargs='*', help="The filenames or paths to the true negative csvs", default=['semmed_tn.csv','mychem_tn.csv','mychem_tn_umls.csv','NDF_TN.csv'])
parser.add_argument("--emb", type=str, help="The filename or path of the emb file generated for your graph", default="graph.emb")
parser.add_argument("--map", type=str, help="The filename or path of the map file generated by EdgelistMaker.py", default="map.csv")
parser.add_argument("-c", "--cutoff", type=int, help="A positive integer for the cutoff of SemMedDB hot counts to include in analysis", default=2)
parser.add_argument("--roc", type=bool, help="A boolian indicating weather or not to print a roc curve for the model", default=False)
parser.add_argument("--type", type=str, help="A string indicating the type of model to use. (options are 'LR' - logistic regression, 'RF' - random forest)", default='RF')
parser.add_argument("-d", "--depth", type=int, help="a positive integer for the maximum depth of trees in the random forest", default=15)
parser.add_argument("-n", "--trees", type=int, help="a positive integer for the number of trees in the random forest", default=2000)
parser.add_argument("--rand", type=bool, help="A boolian indicating weather or not to print a cutoffplot for random pairings od drugs and diseases", default=False)
parser.add_argument("-s", "--save", type=str, help="A string indicating the path/filename to save the model as.", default="data/RandomForestModel.pkl")

args = parser.parse_args()

if not args.type.upper() in ['LR','RF']:
    print('Model selection not valid. Using random forest...')
    args.type = 'RF' 






class LogReg():
    """
    This class takes the output of node2vec and trains a logistic regression model using true positive and true negative data

    :param node_vec_file: A string containing the file name of the .emb output file generated by node2vec.
    :param map_file: A string containing the file name of the map file that converts between curie ids and the corresponding integers used for node2vec
    :param TP_name_list: A list of strings containing the csvs with the True Positives in it.
    :param TN_name_list: A list of strings containing the csvs with the True Negatives in it.
    :param cutoff: A positive integer indicating the cutoff of SemMedDB hit counts to include (2 means 2 or more hits included)
    """

    def __init__(self, node_vec_file = 'q_1_p_1_e_5_d_128_l_100_r_15_directed.emb', map_file = 'map.csv', TP_name_list = ['c_tp2.csv','NDF_TP2.csv'], TN_name_list = ['c_tn2.csv','NDF_TN2.csv'], cutoff = 2):

        # Loads the generated emb file and the curie -> integer id map file
        self.node_vec = pd.read_csv(node_vec_file, sep = ' ', skiprows=1, header = None, index_col=None)
        map_df = pd.read_csv(map_file, index_col=None)
        self.map_df = map_df

        # Sorts the rows of the vectorized nodes by integer id for quick retrieval
        self.node_vec = self.node_vec.sort_values(0).reset_index(drop=True)

        map_dict = {}
        drug_ids = []
        dis_ids = []

        # Build dict mapping curie -> id
        for row in range(len(map_df)):
            map_dict[map_df['curie'][row]] = map_df['id'][row]

        TP_list = []
        TN_list = []

        # generate list of true positive and true negative data frames
        for i in range(len(TP_name_list)):
            TP_list += [pd.read_csv(TP_name_list[i],index_col=None)]

        for i in range(len(TN_name_list)):
            TN_list += [pd.read_csv(TN_name_list[i],index_col=None)]

        y = []
        X = []

        y1 = []
        X1 = []

        y2 = []
        X2 = []

        c = 0

        id_list = []
        id_list_dict = dict()

        # Generate true negative training set by concatinating source-target pair vectors
        for TN in TN_list:
            for row in range(len(TN)):
                if 'count' in list(TN):
                    if int(TN['count'][row]) < cutoff:
                        continue
                try:
                    source_id = map_dict[TN['source'][row]]
                    source_curie = TN['source'][row]
                    target_id = map_dict[TN['target'][row]]
                    target_curie = TN['target'][row]
                except KeyError:
                    c += 1
                    continue

                if (source_curie, target_curie) not in id_list_dict:
                    id_list += [[source_curie, target_curie]]
                    id_list_dict[source_curie, target_curie] = 0
                    X2 += [list(self.node_vec.iloc[source_id,1:]) + list(self.node_vec.iloc[target_id,1:])]

        # Generate true positive training set by concatinating source-target pair vectors
        for TP in TP_list:
            for row in range(len(TP)):
                if 'count' in list(TP):
                    if int(TP['count'][row]) < cutoff + 10:
                        continue
                try:
                    source_id = map_dict[TP['source'][row]]
                    source_curie = TP['source'][row]
                    target_id = map_dict[TP['target'][row]]
                    target_curie = TP['target'][row]
                except KeyError:
                    c += 1
                    continue

                if (source_curie, target_curie) not in id_list_dict:
                    id_list += [[source_curie, target_curie]]
                    id_list_dict[source_curie, target_curie] = 1
                    X1 += [list(self.node_vec.iloc[source_id,1:]) + list(self.node_vec.iloc[target_id,1:])]

        # Assign 0 to negatives and 1 to positives
        y1 = [1]*len(X1)
        y2 = [0]*len(X2)

        # Convert to numpy arrays and concatinate
        X1 = np.array(X1)
        y1 = np.array(y1)
        X2 = np.array(X2)
        y2 = np.array(y2)
        X = np.concatenate((X1,X2))
        y = np.concatenate((y1,y2))

        self.Xtp = X1
        self.Xtn = X2

        # Assign to class attribute
        self.X = X
        self.y = y
        self.id_list = id_list

    
    def plot_cutoff(self, dfs, title_post = ["Random Pairings", "True Negatives", "True Positives"], print_flag=True):
        """
        This plots the treats classification rate for every cutoff of a whole %

        :df: A pandas dataframe containing the predictions
        :title_post: A string containing the Last part of the title
        :print_flag: A boolian indicating whether to print exact numbers for the last 20% of cutoffs or not
        """
        if type(dfs) != list:
            dfs = [dfs]

        color = ["xkcd:dark magenta","xkcd:dark turquoise","xkcd:azure","xkcd:purple blue","xkcd:scarlet",
            "xkcd:orchid", "xkcd:pumpkin", "xkcd:gold", "xkcd:peach", "xkcd:neon green", "xkcd:grey blue"]
        c = 0

        for df in dfs:
            cutoffs = [x/100 for x in range(101)]
            cutoff_n = [df["treat_prob"][df["treat_prob"] >= cutoff].count()/len(df) for cutoff in cutoffs]

            plt.plot(cutoffs,cutoff_n,color[c],label=title_post[c])
            if print_flag:
                with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                    print("\n",title_post[c], ":\n")
                    print(pd.DataFrame({"cutoff":cutoffs[80:],"count":cutoff_n[80:]}))
            c += 1
        plt.xlim([0, 1])
        plt.ylim([0, 1])
        plt.xlabel('Cutoff Prob')
        plt.ylabel('Rate of Postitive Predictions')
        plt.title('Prediction Rates of Treats Class')
        plt.legend(loc="lower left")
        plt.show()

        


    def rand_rate(self, n, drug_csv, disease_csv):
        """
        This generates random drug disease pairings for use in cutoff plot.

        :param n: An integer indicating the number of random pairs to generate
        :param drug_csv: A string containing the path/filename of a csv containing the drug curie ids
        :param disease_csv: A string containing the path/filename of a csv containing the disease curie ids
        """

        # Load the csvs and extract the curie ids
        drug_df = pd.read_csv(drug_csv, index_col=None)
        disease_df = pd.read_csv(disease_csv, index_col=None)
        drugs = list(drug_df["id"])
        diseases = list(disease_df["id"])

        # generate random seed from time
        #random.seed(1123581113)
        random.seed(int(time.time()/100))

        # get number of drug and disease ids
        drug_n = len(drug_df)
        dis_n = len(disease_df)

        # initialize lists and dicts
        X_list = []
        data_list = []
        c = 0

        # Find all permutations
        perms = list(itertools.product(range(drug_n),range(dis_n)))
        for idx in random.sample(perms, 2*n):
            # get curie ids
            source_curie = drugs[idx[0]]
            target_curie = diseases[idx[1]]
            
            # get uids
            source_id = self.map_df.loc[self.map_df['curie'] == source_curie, 'id']
            target_id = self.map_df.loc[self.map_df['curie'] == target_curie, 'id']
            
            # if id was found
            if len(source_id) >0 and len(target_id)>0:
                # store id and count up for successful mapping
                source_id = source_id.iloc[0]
                target_id = target_id.iloc[0]
                c+=1
                
                # Sore results in list
                X_list += [list(self.node_vec.iloc[source_id,1:]) + list(self.node_vec.iloc[target_id,1:])]
                data_list += [[source_curie,target_curie]]
            # if found n successful mappings break loop
            if c == n:
                break

        # convert lists to array/dataframe for use later
        self.X2 = np.array(X_list)
        self.data = pd.DataFrame(data_list, columns=['source','target'])
        

    def max_lr_f1(self, C_flag = False, save = ""):
        """
        This uses LogisticRegressionCV to find the maximum mean f1 score using by adjusting the C parameter

        :param C_flag: A boolian indicating what to output from the function. (if False output the max mean f1, if True output the C value used to find the maximum mean f1 score)
        """

        # seeds random state from time
        random_state = np.random.RandomState(int(time.time()))
        np.random.seed(int(time.time()/100))

        # Uncomment if you want to seed random state from iteger instead (to be able to repeat exact results)
        #random_state = np.random.RandomState(11235813)
        #np.random.seed(112358)

        # Sets up 10-fold cross validation set
        cv = ms.StratifiedKFold(n_splits=10, random_state=random_state, shuffle=True)
        
        # Sets and fits Logistic Regression Model
        model2 = lm.LogisticRegressionCV(class_weight='balanced', random_state = random_state, cv = cv, n_jobs=-1, scoring = 'f1')
        fitModel = model2.fit(self.X, self.y)
        
        
        # saves the model
        if len(save)>0:
            joblib.dump(fitModel, save)
        
        # returns the c value or f1 score
        if C_flag:
            return model2.C_[0]
        else:
            return model2.scores_[1].mean(axis=0).max()

    def lr_roc_curve(self,C):
        """
        This generates a roc curve using logistic regression and 10 fold crossvalidation

        :param C: The C parameter used for the logistic regression.
        """
        # sets model
        model = lm.LogisticRegression(class_weight='balanced', C = C)

        # seeds random state from time
        random_state = np.random.RandomState(int(time.time()))
        np.random.seed(int(time.time()/100))

        # Uncomment if you want to seed random state from iteger instead (to be able to repeat exact results)
        #random_state = np.random.RandomState(11235813)
        #np.random.seed(112358)

        # Sets up 10-fold cross validation set
        cv = ms.StratifiedKFold(n_splits=10, random_state=random_state, shuffle=True)

        tprs = []
        aucs = []
        f1s = []
        mean_fpr = np.linspace(0, 1, 100)

        i = 0

        # Creates a shuffled index for X and y
        shuffled_idx = np.arange(len(self.y))
        np.random.shuffle(shuffled_idx)

        # Uncomment if you want it to find and print the mean f1 score
        #test_f1_mean = np.mean(ms.cross_val_score(model, self.X[shuffled_idx], self.y[shuffled_idx], cv=10, n_jobs=-1, scoring='f1'))
        #print('using cross val score F1 = %0.4f' % (test_f1_mean))

        # Calculates and plots the roc cureve for each set in 10-fold cross validation
        for train, test in cv.split(self.X, self.y):
            model_i = model.fit(self.X[train], self.y[train])
            probas_ = model_i.predict_proba(self.X[test])
            pred = model_i.predict(self.X[test])
            f1 = met.f1_score(self.y[test], pred, average='binary')
            f1s.append(f1)
            # Compute ROC curve and area the curve
            fpr, tpr, thresholds = met.roc_curve(self.y[test], probas_[:, 1])
            tprs.append(sci.interp(mean_fpr, fpr, tpr))
            tprs[-1][0] = 0.0
            roc_auc = met.auc(fpr, tpr)
            aucs.append(roc_auc)
            plt.plot(fpr, tpr, lw=1, alpha=0.3,
                    label='ROC fold %d (AUC = %0.4f, F1 = %0.4f)' % (i+1, roc_auc, f1))

            i += 1

        # Plots the 50/50 line
        plt.plot([0, 1], [0, 1], linestyle='--', lw=2, color='r',
                label='Coin Flip', alpha=.8)

        # Finds and plots the mean roc curve and mean f1 score
        mean_tpr = np.mean(tprs, axis=0)
        mean_f1 = np.mean(f1s)
        mean_tpr[-1] = 1.0
        mean_auc = met.auc(mean_fpr, mean_tpr)
        std_auc = np.std(aucs)
        plt.plot(mean_fpr, mean_tpr, color='b',
                label=u'Mean ROC (AUC = %0.4f \u00B1 %0.4f, \n        \
                    Mean F1 = %0.4f)' % (mean_auc, std_auc, mean_f1),
                lw=2, alpha=.8)

        # Finds and plots the +- standard deviation for roc curve
        std_tpr = np.std(tprs, axis=0)
        tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
        tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
        plt.fill_between(mean_fpr, tprs_lower, tprs_upper, color='grey', alpha=.2,
                        label=r'$\pm$ 1 std. dev.')

        # Sets legend, limits, labels, and displays plot
        plt.xlim([-0.05, 1.05])
        plt.ylim([-0.05, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic')
        plt.legend(loc="lower right")
        plt.show()

    def classify_rf(self, max_depth=64, n_estimators=1000, max_features="sqrt", roc_flag = False, rand_flag = False, save = ""):
        """
        This uses LogisticRegressionCV to find the maximum mean f1 score using by adjusting the C parameter

        :param C_flag: A boolian indicating what to output from the function. (if False output the max mean f1, if True output the C value used to find the maximum mean f1 score)
        """

        # seeds random state from time
        random_state = np.random.RandomState(int(time.time()))
        np.random.seed(int(time.time()/100))

        # Uncomment if you want to seed random state from iteger instead (to be able to repeat exact results)
        #random_state = np.random.RandomState(11235813)
        #np.random.seed(112358)

        # Sets and fits Random ForestModel
        model2 = ensemble.RandomForestClassifier(class_weight='balanced', max_depth=max_depth, max_leaf_nodes=None, n_estimators=n_estimators, min_samples_leaf=1, min_samples_split=2, max_features=max_features, n_jobs=-1)
        fitModel = model2.fit(self.X, self.y)

        # saves the model
        if len(save) > 0:
            joblib.dump(fitModel, save)


        if rand_flag:
            # Generate random drug-disease pairs
            rand_n=10000
            self.rand_rate(rand_n,"data/drugs.csv","data/diseases.csv")

            # Get random pairs cutoff rates
            probas_rand = fitModel.predict_proba(self.X2)

            self.data["treat_prob"] = [pr[1] for pr in probas_rand]
            #print(self.data.sort_values("treat_prob", ascending = False).reset_index(drop=True))
            

            # Get true positive cutoff rates
            probas_tp = fitModel.predict_proba(self.Xtp)   

            # Get true negative cutoff rates
            probas_tn = fitModel.predict_proba(self.Xtn)
            
            # Plot the cutoff rates together
            self.plot_cutoff([pd.DataFrame({"treat_prob":[pr[1] for pr in probas_rand]}),
                pd.DataFrame({"treat_prob":[pr[1] for pr in probas_tp]}),
                pd.DataFrame({"treat_prob":[pr[1] for pr in probas_tn]})],
                ["Random Pairs",
                "True Positives", 
                "True Negatives"])

        if roc_flag:
            model = ensemble.RandomForestClassifier(class_weight='balanced', max_depth=max_depth, max_leaf_nodes=None, n_estimators=n_estimators, min_samples_leaf=1, min_samples_split=2, max_features=max_features, n_jobs=-1)

            # Sets up 10-fold cross validation set
            cv = ms.StratifiedKFold(n_splits=10, random_state=random_state, shuffle=True)

            tprs = []
            aucs = []
            f1s = []
            mean_fpr = np.linspace(0, 1, 100)

            i = 0

            # Creates a shuffled index for X and y
            shuffled_idx = np.arange(len(self.y))
            np.random.shuffle(shuffled_idx)

            # Uncomment if you want it to find and print the mean f1 score
            #test_f1_mean = np.mean(ms.cross_val_score(model, self.X[shuffled_idx], self.y[shuffled_idx], cv=10, n_jobs=-1, scoring='f1'))
            #print('using cross val score F1 = %0.4f' % (test_f1_mean))

            prob_list = []

            # Calculates and plots the roc cureve for each set in 10-fold cross validation
            for train, test in cv.split(self.X, self.y):
                model_i = model.fit(self.X[train], self.y[train])
                probas_ = model_i.predict_proba(self.X[test])
                pred = model_i.predict(self.X[test])
                f1 = met.f1_score(self.y[test], pred, average='binary')
                f1s.append(f1)
                # Compute ROC curve and area the curve
                #prob_list += [pd.DataFrame({"treat_prob":[pr[1] for pr in probas_]})]
                fpr, tpr, thresholds = met.roc_curve(self.y[test], probas_[:, 1])
                tprs.append(sci.interp(mean_fpr, fpr, tpr))
                tprs[-1][0] = 0.0
                roc_auc = met.auc(fpr, tpr)
                aucs.append(roc_auc)
                plt.plot(fpr, tpr, lw=1, alpha=0.3,
                        label='ROC fold %d (AUC = %0.4f, F1 = %0.4f)' % (i, roc_auc, f1))

                i += 1

            # Plots the 50/50 line
            plt.plot([0, 1], [0, 1], linestyle='--', lw=2, color='r',
                    label='Coin Flip', alpha=.8)

            # Finds and plots the mean roc curve and mean f1 score
            mean_tpr = np.mean(tprs, axis=0)
            mean_f1 = np.mean(f1s)
            mean_tpr[-1] = 1.0
            mean_auc = met.auc(mean_fpr, mean_tpr)
            std_auc = np.std(aucs)
            plt.plot(mean_fpr, mean_tpr, color='b',
                    label=u'Mean ROC (AUC = %0.4f \u00B1 %0.4f, \n        \
                        Mean F1 = %0.4f)' % (mean_auc, std_auc, mean_f1),
                    lw=2, alpha=.8)

            # Finds and plots the +- standard deviation for roc curve
            std_tpr = np.std(tprs, axis=0)
            tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
            tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
            plt.fill_between(mean_fpr, tprs_lower, tprs_upper, color='grey', alpha=.2,
                            label=r'$\pm$ 1 std. dev.')

            # Sets legend, limits, labels, and displays plot
            plt.xlim([-0.05, 1.05])
            plt.ylim([-0.05, 1.05])
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title('Receiver Operating Characteristic')
            plt.legend(loc="lower right")
            plt.show()

            #self.plot_cutoff(prob_list,["CV " + str(num) for num in range(len(prob_list))])
        

    def test_f1(self):
        print(self.max_lr_f1())

    def test_roc(self):
        self.lr_roc_curve(self.max_lr_f1(True))

if __name__ == "__main__":
    lr = LogReg(node_vec_file = args.emb, map_file = args.map, TP_name_list = args.tp, TN_name_list = args.tn, cutoff = args.cutoff)
    if args.type.upper() == 'LR':
        c = lr.max_lr_f1(C_flag = True,save=args.save)
        if(args.roc):
            lr.lr_roc_curve(c)
    elif args.type.upper() == 'RF':
        lr.classify_rf(save=args.save,roc_flag=args.roc,rand_flag=args.rand,max_depth=args.depth,n_estimators=args.trees)





