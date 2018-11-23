import numpy as np
import pandas as pd
import os
import zipfile
import urllib.request

def loadData(data_dir):
    '''
    :param data_dir: where the data is loaded
    :return: dataframe with expense info
    '''

    # data directory
    # TODO: file loading can be improved by restricting only to files >= start_year
    files = os.listdir(data_dir)
    df_list = []

    # create datatype dictionary
    dtype_dic = {'txNomeParlamentar': str,
                 'idecadastro': str,
                 'nuCarteiraParlamentar': str,
                 'nuLegislatura': str,
                 'sgUF': str,
                 'sgPartido': str,
                 'codLegislatura': str,
                 'numSubCota': str,
                 'txtDescricao': str,
                 'numEspecificacaoSubCota': str,
                 'txtDescricaoEspecificacao': str,
                 'txtFornecedor': str,
                 'txtCNPJCPF': str,
                 'txtNumero': str,
                 'indTipoDocumento': str,
                 'datEmissao': str,
                 'vlrDocumento': np.float32,
                 'vlrGlosa': np.float32,
                 'vlrLiquido': np.float32,
                 'numMes': int,
                 'numAno': int,
                 'numParcela': int,
                 'txtPassageiro': str,
                 'txtTrecho': str,
                 'numLote': int,
                 'numRessarcimento': str,
                 'vlrRestituicao': str,
                 'nuDeputadoId': str,
                 'ideDocumento': str}

    parse_dates = ['datEmissao']

    for f in files:

        # check if file is a .csv.zip
        if f[-8:] != '.csv.zip':
            continue

        # build path
        filepath = data_dir + f

        # creat zip object
        zfile = zipfile.ZipFile(filepath)

        # iterate over files in zip
        for finfo in zfile.infolist():

            # check if csv
            if finfo.filename[-4:] == '.csv':
                # read file, create dataframe, and append to dataframe list
                csv = zfile.open(finfo)

                df_list.append(pd.read_csv(csv, sep=';', decimal=",", parse_dates=parse_dates, dtype=dtype_dic))

    # append to one mega dataframe
    df = pd.concat(df_list, ignore_index=True)

    # now we fixe dates
    def convert_date(x):
        try:
            return pd.to_datetime(x)
        except:
            return x

    # fix things that were loaded as strings vs numbers
    df.iloc[:, 26] = df.iloc[:, 26].apply(np.float64)
    df['datEmissao'] = df['datEmissao'].apply(convert_date)

    # delete list to save memory
    del df_list

    # We now fix entries whose date 'dataEmissao' do not make sense -- we will relabel them using 'numMes' and 'numAno',
    # and put it to the start of the month.
    bad_ix = df.loc[df['datEmissao'].apply(lambda x: True if type(x) == str else False)].index.tolist()
    bad_ix += df.loc[df['datEmissao'].apply(
        lambda x: True if (type(x) != str) and ((x.year > 2018) or (x.year < 2009)) else False)].index.tolist()
    bad_ix = list(set(bad_ix))
    for ix in bad_ix:
        year = str(df.loc[ix, 'numAno'])
        month = str(df.loc[ix, 'numMes'])
        date = pd.to_datetime(year + '-' + month + '-' + '01')
        df.loc[ix, 'datEmissao'] = date

    # produce valid names
    allNames = list(set(list(df['txNomeParlamentar'])))

    # get names that only have one word
    badNames = [n for n in allNames if len(n) < 5 or (('-' in n) and (' ') not in n)]

    df = df[~df['txNomeParlamentar'].isin(badNames)]
    
    # translate column names
    # create datatype dictionary
    translate_dic = {'txNomeParlamentar': 'name',
                 'idecadastro': 'id',
                 'nuCarteiraParlamentar': 'docId',
                 'nuLegislatura': 'termStart',
                 'sgUF': 'state',
                 'sgPartido': 'party',
                 'codLegislatura': 'congressNum',
                 'numSubCota': 'categoryId',
                 'txtDescricao': 'categoryTxt',
                 'numEspecificacaoSubCota': 'subCategoryId',
                 'txtDescricaoEspecificacao': 'subCategoryTxt',
                 'txtFornecedor': 'vendorName',
                 'txtCNPJCPF': 'vendorId',
                 'txtNumero': 'receiptId',
                 'indTipoDocumento': 'receiptType',
                 'datEmissao': 'expenseDate',
                 'vlrDocumento': 'valueReceipt',
                 'vlrGlosa': 'valueNotReimb',
                 'vlrLiquido': 'valueReimb',
                 'numMes': 'month',
                 'numAno': 'year',
                 'numParcela': 'paymentNum',
                 'txtPassageiro': 'passengerName',
                 'txtTrecho': 'trip',
                 'numLote': 'batch',
                 'numRessarcimento': 'numReimb',
                 'vlrRestituicao': 'valueUnclear',
                 'nuDeputadoId': 'congId',
                 'ideDocumento': 'ideDocumento'}
    
    # rename columns
    df.rename(columns=translate_dic,inplace=True)
    
    # rename categoryTxt
    translate_dic = {'LOCOMOÇÃO, ALIMENTAÇÃO E  HOSPEDAGEM': 'Transport, food, and lodging',
                     'Emissão Bilhete Aéreo' : 'Airline Ticket Issue',
                     'CONSULTORIAS, PESQUISAS E TRABALHOS TÉCNICOS.' : 'Consulting, research, and technical activities',
                     'MANUTENÇÃO DE ESCRITÓRIO DE APOIO À ATIVIDADE PARLAMENTAR' : 'Maintenance of an office that supports parliamentary activity',
                     'HOSPEDAGEM ,EXCETO DO PARLAMENTAR NO DISTRITO FEDERAL.' : 'Lodging, except for congresspeople from the Distrito Federal',
                     'DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR.' : 'Disclosure and advertisement of parliamentary activity',
                     'FORNECIMENTO DE ALIMENTAÇÃO DO PARLAMENTAR' : 'Food for the congressperson',
                     'LOCAÇÃO OU FRETAMENTO DE EMBARCAÇÕES' : 'Boat rental or chartering',
                     'AQUISIÇÃO DE MATERIAL DE ESCRITÓRIO.' : 'Office supplies',
                     'SERVIÇO DE TÁXI, PEDÁGIO E ESTACIONAMENTO' : 'Taxi services, tolls, and parking',
                     'SERVIÇOS POSTAIS' : 'Postal services',
                     'PASSAGENS TERRESTRES, MARÍTIMAS OU FLUVIAIS' : 'Overland, maritime, or river transport tickets',
                     'TELEFONIA' : 'Phone services',
                     'PASSAGENS AÉREAS' : 'Airline tickets',
                     'LOCAÇÃO DE VEÍCULOS AUTOMOTORES OU FRETAMENTO DE EMBARCAÇÕES' : 'Car or boat rental/chartering',
                     'AQUISIÇÃO OU LOC. DE SOFTWARE SERV. POSTAIS ASS.' : 'Purchase or leasing of software services and postal (?) assistance',
                     'ASSINATURA DE PUBLICAÇÕES' : 'Publication subscription',
                     'COMBUSTÍVEIS E LUBRIFICANTES.' : 'Fuel and lubricants',
                     'LOCAÇÃO OU FRETAMENTO DE AERONAVES' : 'Rental or chartering of aircrafts',
                     'LOCAÇÃO OU FRETAMENTO DE VEÍCULOS AUTOMOTORES' : 'Rental or chartering of motor vehicles',
                     'PARTICIPAÇÃO EM CURSO, PALESTRA OU EVENTO SIMILAR' : 'Participation in course, lecture, or similar event',
                     'SERVIÇO DE SEGURANÇA PRESTADO POR EMPRESA ESPECIALIZADA.' : 'Security services provided by a specialized company'}
    
    df['categoryTxt'] = df['categoryTxt'].apply(lambda x : translate_dic[x])
    
    # rename subCategoryTxt
    translate_dic = {'Embarcações' : 'Water vessels', 
                     'Aeronaves' : 'Aircrafts', 
                     'Veículos Automotores' : 'Motor vehicles', 
                     'Sem especificações' : 'Not specified'}
    
    df.loc[df['subCategoryTxt'].notnull(),'subCategoryTxt'] = df['subCategoryTxt'][df['subCategoryTxt'].notnull()].apply(lambda x: translate_dic[x])    

    return df

def formatdf(df,start_date=2009,min_occur_name = 1e2,min_occur_expenditure = .015):
    '''
    :param: df: dataframe with spending data
    :param start_date: cut the dataframe above a certain data
    :param min_occur_name: minimum number of expenditures per congressman
    :param min_occur_expenditure: minimum number of expenditures per category
    :return: dfS: data restricted dataframe
    '''

    # keep only purchases after a certain date
    df = df[df['year'] >= start_date]

    # keep only congress members with at least min_occur_name expenses
    counts = df.groupby('id').size()
    keep_list = list(counts[counts>=min_occur_name].index)
    df = df[df['id'].isin(keep_list)]
    
    # keep only categories with a minimum number of expenses
    counts = df.groupby('categoryTxt').size()
    counts = counts/counts.sum()
    keep_list = list(counts[counts>=min_occur_expenditure].index)
    df = df[df['categoryTxt'].isin(keep_list)]
    
    # keep only certain categories
    keep_cat = ['name',
                'id',
                'termStart',
                'state',
                'party',
                'congressNum',
                'categoryId',
                'categoryTxt',
                'vendorId',
                'vendorName',
                'valueReimb',
                'expenseDate',
                'trip',
                'month',
                'year']
    
    return df[keep_cat]

def cleanupAirFare(df):
    '''
    This function cleans up some of the duplicate airfares that were reimbursed.
    ATTENTION: This may affect your analyses, especially trip distances
    '''
    # restrict to airline ticket issues
    dfAir = df[df['categoryTxt']=='Airline Ticket Issue']
    
    # reduce size
    dfAir = dfAir[['receiptId','vendorName','passengerName','trip','valueReceipt','valueNotReimb','valueReimb']]
    
    # keep only tickets that are negative (i.e., reimbursements)
    neg_receipt = dfAir.groupby('receiptId')['valueReimb'].min()
    neg_receipt = neg_receipt[neg_receipt<0]
    list_neg = list(neg_receipt.index)
    
    dfAir2 = dfAir[dfAir['receiptId'].isin(list_neg)] # get receipts that appear with negative values

    # Out of the receipts with negative values, find those that are duplicates
    duplicate_receipt = dfAir2.groupby('receiptId').size()
    list_duplicate = list((duplicate_receipt[(duplicate_receipt <=15 )&(duplicate_receipt >1 )]).index)

    # select only the receipts with duplicate Ids, and that appear once with a negative value
    dfAir2 = dfAir2[dfAir2['receiptId'].isin(list_duplicate)].reset_index()

    correct_vals = dfAir2.groupby(['receiptId','passengerName'])['index','valueReimb'].agg({'index' : lambda x: list(x), 
                                                           'valueReimb' : 'sum'})

    # indices of the original dataframe that will be cleaned up
    keep_index = [x[0] for x in correct_vals['index'].values]
    #drop_index = [x[1:] for x in correct_vals['index'].values]
    drop_index = [l for x in correct_vals['index'].values for l in x[1:]]
    true_reimb = list(correct_vals['valueReimb'].values)
    
    # subsitute in dataframe
    df.loc[keep_index,'valueReimb'] = true_reimb
    
    # drop repeated indices and return
    return df.drop(drop_index)


def downloadData(data_dir):
    '''
    :param data_dir: where the data is supposed to be saved
    '''
    
    # years: 2009-2017
    years = [str(i) for i in range(2009,2019,1)]
    for y in years:
        url = 'http://www.camara.leg.br/cotas/Ano-'+y+'.csv.zip'
        
        # retrieve file
        file_name = data_dir+'Ano-'+y+'.csv.zip'
        print('Downloading year '+y+'...')
        urllib.request.urlretrieve(url, file_name)
        
    print('Done!')