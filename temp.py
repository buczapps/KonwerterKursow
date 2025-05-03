import pandas as pd

# Przykład pierwszego DataFrame
data1 = {'Data': ['2025-05-01', '2025-05-02', '2025-05-03', '2025-05-04'],
         'Kurs_A': [4.30, 4.32, 4.35, 4.33]}
df1 = pd.DataFrame(data1)
df1['Data'] = pd.to_datetime(df1['Data'])
df1 = df1.set_index('Data')
print("DataFrame df1:")
print(df1)
print("\n")

# Przykład drugiego DataFrame
data2 = {'Data': ['2025-05-02', '2025-05-03', '2025-05-04', '2025-05-05'],
         'Kurs_B': [1.10, 1.12, 1.11, 1.13]}
df2 = pd.DataFrame(data2)
df2['Data'] = pd.to_datetime(df2['Data'])
df2 = df2.set_index('Data')
print("DataFrame df2:")
print(df2)
print("\n")

# Połączenie DataFrames na podstawie indeksu (daty)
df_polaczony = pd.merge(df1, df2, left_index=True, right_index=True, how='inner')
print("Połączony DataFrame:")
print(df_polaczony)
print("\n")

# Przemnożenie kolumn z kursami
df_polaczony['Kurs_Pomnozony'] = df_polaczony['Kurs_A'] * df_polaczony['Kurs_B']
print("DataFrame z przemnożonymi kursami:")
print(df_polaczony)