#!/usr/bin/env python3
"""
Model information and selection utility for LLM translation
"""
import os
from typing import Dict, List

# Latest Gemini models (as of December 2024)
GEMINI_MODELS = {
    "gemini-2.0-flash-exp": {
        "name": "Gemini 2.0 Flash (Experimental)",
        "description": "最新实验版本，速度最快，支持最新功能",
        "speed": "最快",
        "quality": "高",
        "cost": "低",
        "recommended_for": "大批量翻译，快速原型"
    },
    "gemini-1.5-pro": {
        "name": "Gemini 1.5 Pro",
        "description": "稳定高质量版本，长上下文支持",
        "speed": "中等",
        "quality": "最高",
        "cost": "中等",
        "recommended_for": "高质量翻译，复杂内容"
    },
    "gemini-1.5-flash": {
        "name": "Gemini 1.5 Flash",
        "description": "平衡速度和质量的选择",
        "speed": "快",
        "quality": "高",
        "cost": "低",
        "recommended_for": "日常翻译，平衡需求"
    }
}

# Other LLM providers
OTHER_MODELS = {
    "openai": {
        "gpt-4o": {
            "name": "GPT-4o",
            "description": "OpenAI 最新多模态模型",
            "speed": "中等",
            "quality": "最高",
            "cost": "高"
        },
        "gpt-4o-mini": {
            "name": "GPT-4o Mini",
            "description": "更快更便宜的 GPT-4o 版本",
            "speed": "快",
            "quality": "高",
            "cost": "低"
        }
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {
            "name": "Claude 3.5 Sonnet",
            "description": "Anthropic 最新高质量模型",
            "speed": "中等",
            "quality": "最高",
            "cost": "中等"
        },
        "claude-3-5-haiku-20241022": {
            "name": "Claude 3.5 Haiku",
            "description": "更快更便宜的 Claude 版本",
            "speed": "最快",
            "quality": "高",
            "cost": "低"
        }
    }
}

def get_recommended_model(priority: str = "quality") -> str:
    """
    Get recommended model based on priority
    
    Args:
        priority: "speed", "quality", or "cost"
    
    Returns:
        Recommended model name
    """
    recommendations = {
        "speed": "gemini-2.0-flash-exp",
        "quality": "gemini-1.5-pro", 
        "cost": "gemini-2.0-flash-exp",
        "balanced": "gemini-1.5-flash"
    }
    
    return recommendations.get(priority, "gemini-2.0-flash-exp")

def list_available_models(provider: str = "gemini") -> Dict:
    """List available models for a provider"""
    if provider == "gemini":
        return GEMINI_MODELS
    elif provider in OTHER_MODELS:
        return OTHER_MODELS[provider]
    else:
        return {}

def print_model_comparison():
    """Print a comparison of available models"""
    print("🤖 可用的 LLM 翻译模型对比")
    print("=" * 60)
    
    print("\n📱 Google Gemini 模型:")
    for model_id, info in GEMINI_MODELS.items():
        print(f"\n🔹 {info['name']} ({model_id})")
        print(f"   描述: {info['description']}")
        print(f"   速度: {info['speed']} | 质量: {info['quality']} | 成本: {info['cost']}")
        print(f"   推荐用途: {info['recommended_for']}")
    
    print(f"\n💡 推荐选择:")
    print(f"   🚀 追求速度: {get_recommended_model('speed')}")
    print(f"   🎯 追求质量: {get_recommended_model('quality')}")
    print(f"   💰 控制成本: {get_recommended_model('cost')}")
    print(f"   ⚖️  平衡需求: {get_recommended_model('balanced')}")

def main():
    """Main function to display model information"""
    print_model_comparison()
    
    print(f"\n🔧 当前配置:")
    current_provider = os.getenv('TRANSLATION_PROVIDER', 'gemini')
    current_model = os.getenv('TRANSLATION_MODEL', 'gemini-2.0-flash-exp')
    print(f"   Provider: {current_provider}")
    print(f"   Model: {current_model}")
    
    if current_provider == 'gemini' and current_model in GEMINI_MODELS:
        model_info = GEMINI_MODELS[current_model]
        print(f"   名称: {model_info['name']}")
        print(f"   描述: {model_info['description']}")

if __name__ == "__main__":
    main()
