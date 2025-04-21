import pandas as pd
import re

# Load the data
file_path = 'paper_with_authors_final.xlsx'
df = pd.read_excel(file_path)

# Function to normalize author names for better matching
def normalize_name(name):
    # Remove any asterisk symbols first
    name = name.replace('*', '')
    # Split name by comma and clean spaces
    parts = [part.strip() for part in name.split(',')]
    
    if len(parts) >= 2:
        # For names in format "Zheng, Yu-Feng" or "Zheng, Yu, Feng"
        last_name = parts[0].lower()
        # Join all other parts and remove punctuation
        first_name = ' '.join(parts[1:]).lower()
        first_name = re.sub(r'[-_\s;]+', '', first_name).strip()
        return f"{last_name}_{first_name}"
    else:
        # For names without commas, just normalize
        return re.sub(r'[-_\s;]+', '', name.lower()).strip()

# Function to check if two author names match based on last name and similar first name
def is_same_author(author1, author2):
    # Exact match check
    if author1 == author2:
        return True
    
    # Process names to handle format variations
    # Split and clean names
    parts1 = [part.strip() for part in author1.replace('*', '').split(',')]
    parts2 = [part.strip() for part in author2.replace('*', '').split(',')]
    
    # If one name doesn't have a comma structure, then not comparable with our method
    if len(parts1) < 2 or len(parts2) < 2:
        return False
    
    # Get last names and check if they match
    last_name1 = parts1[0].lower()
    last_name2 = parts2[0].lower()
    
    if last_name1 != last_name2:
        return False  # Last names don't match
    
    # Clean and join first names (removing hyphens, spaces)
    first_name1 = ''.join(re.sub(r'[-_\s;]+', '', ' '.join(parts1[1:]).lower()))
    first_name2 = ''.join(re.sub(r'[-_\s;]+', '', ' '.join(parts2[1:]).lower()))
    
    # If first names are identical after normalization
    if first_name1 == first_name2:
        return True
    
    # Check if one name contains the other (for handling abbreviated vs full names)
    # This is intentionally limited to avoid false positives like Wei vs Weiwei
    # Only match if lengths are very similar or one is a clear subset
    len_diff = abs(len(first_name1) - len(first_name2))
    
    # Only consider as potential match if length difference is small
    if len_diff <= 2:
        return first_name1 in first_name2 or first_name2 in first_name1
        
    return False

# Function to mark corresponding authors with an asterisk
def mark_corresponding_authors(row):
    if pd.isna(row['通讯作者']):
        return row['全部论文作者']  # Return authors column unchanged if no corresponding authors
    
    corresponding_authors = [author.strip() for author in str(row['通讯作者']).split(';')]
    all_authors = [author.strip() for author in str(row['全部论文作者']).split(';')]
    
    # Add asterisk to corresponding authors
    marked_authors = []
    for author in all_authors:
        # 检查作者名字是否已经有星号标记
        if author.endswith('*'):
            # 如果已经有星号，直接添加不做改变
            marked_authors.append(author)
        elif any(is_same_author(author, ca) for ca in corresponding_authors):
            # 使用改进的名称匹配识别通讯作者
            marked_authors.append(f"{author}*")
        else:
            marked_authors.append(author)
    
    return '; '.join(marked_authors)

# Apply the function to create a new column
df['标记作者'] = df.apply(lambda row: mark_corresponding_authors(row), axis=1)

# Replace the original authors column with the marked version
df['全部论文作者'] = df['标记作者']
df.drop('标记作者', axis=1, inplace=True)

# 删除"通讯作者"和"处理状态"两列
if '通讯作者' in df.columns:
    df.drop('通讯作者', axis=1, inplace=True)
    print("已删除'通讯作者'列")

if '处理状态' in df.columns:
    df.drop('处理状态', axis=1, inplace=True)
    print("已删除'处理状态'列")

# Save the updated data
df.to_excel('paper_with_authors_updated.xlsx', index=False)

print("处理完成。通讯作者已在'全部论文作者'列中用星号(*)标记。")
