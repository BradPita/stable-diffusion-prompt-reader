import json
from ..format.base_format import BaseFormat

class SimpAI(BaseFormat):
    NAME = "simpAI"

    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        self._parse_simpai()

    def _parse_simpai(self):
        try:
            # 检查是否存在 UserComment 
            if "UserComment" in self._info:
                raw_data = self._info["UserComment"]
                
                # 清除可能存在的字节乱码或空字符
                if isinstance(raw_data, bytes):
                    raw_data = raw_data.decode('utf-8', errors='ignore').replace('\x00', '')
                
                # 将文本解析为 JSON 字典
                data = json.loads(raw_data)
                
                # 提取 simpAI 的参数映射到标准属性
                self._positive = data.get("Prompt", "")
                self._negative = data.get("Negative Prompt", "")
                
                # 拼装底部的设置参数信息
                settings = []
                if "Steps" in data: settings.append(f"Steps: {data['Steps']}")
                if "Sampler" in data: settings.append(f"Sampler: {data['Sampler']}")
                if "Seed" in data: settings.append(f"Seed: {data['Seed']}")
                if "Base Model" in data: settings.append(f"Model: {data['Base Model']}")
                if "Resolution" in data: settings.append(f"Size: {data['Resolution']}")
                
                self._setting = ", ".join(settings)
                
                # 完整保留原始 JSON 数据
                self._raw = str(raw_data)
        except Exception as e:
            print(f"解析 simpAI 数据失败: {e}")
