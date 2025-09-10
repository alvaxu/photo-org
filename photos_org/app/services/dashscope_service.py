"""
家庭单机版智能照片整理系统 - DashScope AI服务
"""
import os
import base64
import json
from typing import Dict, List, Optional, Any
import httpx
from app.core.config import settings
from app.core.logging import get_logger


class DashScopeService:
    """
    DashScope AI服务类
    负责与DashScope Qwen-VL模型进行交互
    """

    def __init__(self):
        """初始化DashScope服务"""
        self.logger = get_logger(__name__)
        self.api_key = os.getenv("DASHSCOPE_API_KEY", settings.dashscope.api_key)
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

        if not self.api_key:
            self.logger.warning("未配置DASHSCOPE_API_KEY，将无法使用AI分析功能")

    def _encode_image(self, image_path: str) -> str:
        """
        将图片转换为base64编码

        Args:
            image_path: 图片文件路径

        Returns:
            base64编码的图片数据
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            self.logger.error(f"图片编码失败 {image_path}: {str(e)}")
            raise Exception(f"图片编码失败: {str(e)}")

    def _call_qwen_vl_api(self, image_base64: str, prompt: str, model: str = "qwen-vl-plus-latest") -> Dict[str, Any]:
        """
        调用Qwen-VL API

        Args:
            image_base64: base64编码的图片
            prompt: 分析提示词
            model: 模型名称

        Returns:
            API响应结果
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "X-DashScope-SSE": "disable"
            }

            data = {
                "model": model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "image": f"data:image/jpeg;base64,{image_base64}"
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                },
                "parameters": {
                    "temperature": 0.1,
                    "max_tokens": 1000,
                    "top_p": 0.8
                }
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.base_url, headers=headers, json=data)

                if response.status_code == 200:
                    result = response.json()
                    return result
                else:
                    self.logger.error(f"DashScope API调用失败: {response.status_code} - {response.text}")
                    raise Exception(f"API调用失败: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Qwen-VL API调用异常: {str(e)}")
            raise Exception(f"API调用异常: {str(e)}")

    def analyze_photo_content(self, image_path: str) -> Dict[str, Any]:
        """
        分析照片内容

        Args:
            image_path: 照片文件路径

        Returns:
            分析结果字典
        """
        try:
            # 编码图片
            image_base64 = self._encode_image(image_path)

            # 构建分析提示词
            prompt = """
请详细分析这张照片的内容，并按照以下格式返回JSON结果：

{
    "description": "照片的详细描述（50-100字）",
    "scene_type": "场景类型（室内/室外/风景/人物/建筑/自然/城市/其他）",
    "objects": ["检测到的主要物体1", "物体2", "物体3"],
    "people_count": 人物数量（数字，0表示无人）,
    "emotion": "照片传达的情感（欢乐/宁静/悲伤/兴奋/怀旧/其他）",
    "activity": "照片中的活动类型（聚会/旅行/工作/学习/休闲/运动/庆祝/其他）",
    "time_period": "时间特征（白天/夜晚/黄昏/黎明/室内光线）",
    "location_type": "地点类型（家庭/户外/旅行/办公室/餐厅/公园/其他）",
    "confidence": 分析置信度（0.0-1.0之间的浮点数）,
    "tags": ["相关标签1", "标签2", "标签3", "标签4", "标签5"]
}

请确保：
1. 所有字段都必须填写，不能为空
2. tags字段至少包含3个标签，最多不超过10个
3. confidence字段反映分析的可靠性
4. 描述要详细但简洁
5. 标签要具体且相关
"""

            # 调用API
            result = self._call_qwen_vl_api(image_base64, prompt)

            # 解析响应
            self.logger.info(f"API响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

            if "output" in result and "text" in result["output"]:
                try:
                    # 尝试解析JSON响应
                    text_content = result["output"]["text"]
                    self.logger.info(f"AI原始响应: {text_content}")

                    # 清理可能的markdown格式
                    if text_content.startswith("```json"):
                        text_content = text_content[7:]
                    if text_content.endswith("```"):
                        text_content = text_content[:-3]

                    analysis_result = json.loads(text_content.strip())

                    # 验证必需字段
                    required_fields = ["description", "scene_type", "objects", "people_count",
                                     "emotion", "activity", "time_period", "location_type",
                                     "confidence", "tags"]

                    for field in required_fields:
                        if field not in analysis_result:
                            raise ValueError(f"缺少必需字段: {field}")

                    # 确保tags是列表
                    if not isinstance(analysis_result["tags"], list):
                        analysis_result["tags"] = [analysis_result["tags"]]

                    # 确保confidence是浮点数
                    analysis_result["confidence"] = float(analysis_result["confidence"])

                    return analysis_result

                except json.JSONDecodeError as e:
                    self.logger.error(f"解析AI响应失败: {text_content}")
                    raise Exception(f"AI响应格式错误: {str(e)}")

            elif "output" in result and "choices" in result["output"]:
                # 处理choices格式的响应
                choice = result["output"]["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]

                    # 处理content数组格式
                    if isinstance(content, list) and len(content) > 0:
                        text_content = content[0].get("text", "")
                    else:
                        text_content = str(content)

                    self.logger.info(f"AI响应内容: {text_content}")

                    # 清理可能的markdown格式
                    if text_content.startswith("```json"):
                        text_content = text_content[7:]
                    if text_content.endswith("```"):
                        text_content = text_content[:-3]

                    # 解析JSON
                    try:
                        analysis_result = json.loads(text_content.strip())

                        # 验证必需字段
                        required_fields = ["description", "scene_type", "objects", "people_count",
                                         "emotion", "activity", "time_period", "location_type",
                                         "confidence", "tags"]

                        for field in required_fields:
                            if field not in analysis_result:
                                raise ValueError(f"缺少必需字段: {field}")

                        # 确保tags是列表
                        if not isinstance(analysis_result["tags"], list):
                            analysis_result["tags"] = [analysis_result["tags"]]

                        # 确保confidence是浮点数
                        analysis_result["confidence"] = float(analysis_result["confidence"])

                        return analysis_result

                    except json.JSONDecodeError as e:
                        self.logger.error(f"解析AI响应JSON失败: {text_content}")
                        raise Exception(f"AI响应JSON格式错误: {str(e)}")

            else:
                self.logger.error(f"未知的API响应格式: {json.dumps(result, indent=2)}")
                raise Exception("API响应格式异常")

        except Exception as e:
            self.logger.error(f"照片内容分析失败 {image_path}: {str(e)}")
            raise Exception(f"照片内容分析失败: {str(e)}")

    def generate_photo_caption(self, image_path: str, style: str = "natural") -> str:
        """
        生成照片标题

        Args:
            image_path: 照片文件路径
            style: 生成风格 (natural/creative/poetic)

        Returns:
            生成的标题
        """
        try:
            image_base64 = self._encode_image(image_path)

            style_prompts = {
                "natural": "请用自然的语言为这张照片写一个简短的标题（10-20字）",
                "creative": "请用富有创意的语言为这张照片写一个吸引人的标题（10-20字）",
                "poetic": "请用诗意的语言为这张照片写一个富有意境的标题（10-20字）"
            }

            prompt = style_prompts.get(style, style_prompts["natural"])

            result = self._call_qwen_vl_api(image_base64, prompt)

            if "output" in result and "text" in result["output"]:
                return result["output"]["text"].strip()
            elif "output" in result and "choices" in result["output"]:
                # 处理choices格式的响应
                choice = result["output"]["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]

                    # 处理content数组格式
                    if isinstance(content, list) and len(content) > 0:
                        text_content = content[0].get("text", "")
                    else:
                        text_content = str(content)

                    return text_content.strip()
            else:
                return "美丽的照片"

        except Exception as e:
            self.logger.error(f"生成照片标题失败 {image_path}: {str(e)}")
            return "美丽的照片"
