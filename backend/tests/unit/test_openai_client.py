import unittest
import os
from unittest.mock import patch
from src.llm_client.openai_client import OpenAIClient
from src.llm_client.base import PromptInterface
from src.configs import Constants

# 除非確認要使用真實的API進行測試(當然會因此擁有額外的開銷)，否則將RUN_REAL_API_TESTS設置為False
RUN_REAL_API_TESTS = os.getenv("RUN_REAL_API_TESTS", "false").lower() == "true"


class TestOpenAIClient(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        if RUN_REAL_API_TESTS:
            self.client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            self.client = OpenAIClient(api_key="fake_api_key")

    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    def test_evaluate_relevance_real(self):
        result = self.client.evaluate_relevance("食品價格上漲")
        self.assertIn(result, ["high", "medium", "low"])

    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    def test_generate_summary_real(self):
        result = self.client.generate_summary("中共解放軍近日在「未宣布」軍演的狀況下，仍大量調動機艦，我國防部10日證實，直言共軍數量非常驚人，散佈位置在第一島鏈與第二島鏈間。對此，我國安高層表示，這是1996年以來最大規模海上軍事行動，參加單位超過90艘，且部署時間應長達70天之久")
        self.assertIn("影響", result)
        self.assertIn("原因", result)

    @unittest.skipIf(not RUN_REAL_API_TESTS, "模擬 API 呼叫，跳過真實測試")
    def test_extract_search_keywords_real(self):
        result = self.client.extract_search_keywords("這篇新聞提到食品價格的波動以及市場的供應鏈問題")
        self.assertGreater(len(result.split()), 0)

    @patch('src.llm_client.openai_client.OpenAIClient._generate_completion')
    def test_evaluate_relevance(self, mock_generate_text):
        mock_generate_text.return_value = 'high'

        result = self.client.evaluate_relevance("食品價格上漲")

        self.assertEqual(result, 'high')

        mock_generate_text.assert_called_once_with(
            PromptInterface(system_content=Constants.Prompt.GPT_RELEVANCE_PROMPT,
                            user_content="食品價格上漲")
        )

    @patch('src.llm_client.openai_client.OpenAIClient._generate_completion')
    def test_generate_summary(self, mock_generate_text):
        mock_generate_text.return_value = '{"影響": "影響描述", "原因": "原因描述"}'

        result = self.client.generate_summary("一篇新聞內容")

        self.assertEqual(result, {"影響": "影響描述", "原因": "原因描述"})

        mock_generate_text.assert_called_once_with(
            PromptInterface(system_content=Constants.Prompt.GPT_SUMMARY_PROMPT,
                            user_content="一篇新聞內容")
        )

    @patch('src.llm_client.openai_client.OpenAIClient._generate_completion')
    def test_extract_search_keywords(self, mock_generate_text):
        mock_generate_text.return_value = '食品 價格'

        result = self.client.extract_search_keywords("一段希望看到的新聞文字")

        self.assertEqual(result, '食品 價格')

        mock_generate_text.assert_called_once_with(
            PromptInterface(system_content=Constants.Prompt.GPT_EXTRACT_PROMPT,
                            user_content="一段希望看到的新聞文字")
        )


if __name__ == '__main__':
    unittest.main()