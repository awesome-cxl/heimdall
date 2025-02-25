import pandas as pd
import re
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter


def parse_average(file_path):
    with open(file_path, 'r') as file:
        log_content = file.read()

    # pattern = re.compile(r"^\s*([\d,]+)\s+br_inst_retired\.all_branches:u", re.MULTILINE)
    # pattern = re.compile(r"^\s*([\d\.\d]+)\s*seconds\s*time\s*elapsed", re.MULTILINE)
    pattern = re.compile(r"^\s*([\d]+)\s*ns", re.MULTILINE)
    matches = pattern.findall(log_content)
    # print(matches)
    values = [float(match.replace(',', '')) for match in matches]
    # df = pd.DataFrame(values, columns=['br_inst_retired.all_branches:u'])
    # average_value = df['br_inst_retired.all_branches:u'].mean()
    # print(f"Average TAKEN cond branches of {file_path}: {average_value:.2f}")
    df = pd.DataFrame(values, columns=['time'])
    average_value = df['time'].mean()
    print(f"Average time of {file_path}: {average_value:.2f}")
    
    return average_value

average_values = {}

access_type_list = ['same_local', 'same_remote', "diff_setter", "diff_getter"]
memory_dev_list = ['DIMM', 'CXL']
for memory_dev in memory_dev_list:
    for access_type in access_type_list:
        file_path = f'./results/{access_type}_{memory_dev}.log'
        key = f'{access_type.capitalize()} {memory_dev}'
        average_values[key] = parse_average(file_path)


avg_branch_df = pd.DataFrame(list(average_values.items()), columns=['config', 'avg_time'])

print(avg_branch_df)

plt.rcParams['font.family'] = 'serif'
plt.figure(figsize=(7, 3))
bars = plt.bar(avg_branch_df['config'], avg_branch_df['avg_time'], color='olivedrab', width=0.7)
# plt.xlabel('Configuration', fontsize=12)
plt.ylabel('Time', fontsize=12)
# plt.title('Branches Executed in Spin Lock', fontsize=12, pad=10)
plt.xticks(rotation=45)

plt.gca().yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
plt.gca().ticklabel_format(style='sci', axis='y', scilimits=(0,0))

plt.savefig(f'./figures/spin_lock_test.pdf', bbox_inches='tight')
plt.close()