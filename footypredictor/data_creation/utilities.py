from os import remove
from pathlib import Path
from config import ROOT_DIR
import os
from unidecode import unidecode
import pyarrow as pa
import pyarrow.parquet as pq

class DataframeMaintenance:
    def remove_accents_from_all_dataframes(self):

        for directory in ['player_data', 'player_data_p90', 'player_data_percentiles', 'player_data_p90_percentiles']:
            for year in os.listdir(f'{ROOT_DIR}/player_data_analysis/{directory}'):
                for league in os.listdir(f'{ROOT_DIR}/player_data_analysis/{directory}/{year}'):
                    table = pq.read_table(f'{ROOT_DIR}/player_data_analysis/{directory}/{year}/{league}')
                    df = table.to_pandas()
                    if df.empty:
                        continue
                    df = self.remove_accents_from_dataframe(df)
                    table = pa.Table.from_pandas(df)
                    pq.write_table(table, f'{ROOT_DIR}/player_data_analysis/{directory}/{year}/{league}')


    def remove_accents_from_dataframe(self, dataframe):

        dataframe = dataframe.copy()
        dataframe['player'] = dataframe['player'].apply(unidecode)
        return dataframe


a = DataframeMaintenance()
a.remove_accents_from_all_dataframes()


