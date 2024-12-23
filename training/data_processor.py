import json
import os

def process_training_data(self, raw_data_path):
    """处理训练数据"""
    try:
        # 读取原始数据
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 转换为训练格式
        processed_data = []
        for item in data:
            processed_item = {
                'input_text': f"症状：{item['symptoms']}\n体征：{item['signs']}",
                'target_text': item['diagnosis']
            }
            processed_data.append(processed_item)
            
        # 保存处理后的数据
        output_path = os.path.join(self.config.DATA_DIR, 'processed_training_data.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
        return len(processed_data)
        
    except Exception as e:
        self.logger.error(f"处理训练数据失败: {str(e)}")
        raise 