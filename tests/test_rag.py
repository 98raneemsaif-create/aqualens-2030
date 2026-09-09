"""Focused algorithm/contract tests; real model proof is src.rag.pipeline."""
import unittest

from src.rag.chunking import make_chunks, narrative_runs, split_text
from src.rag.retrieval import e5_inputs, rrf, tokens
from src.rag.generation import Answer, Statement, SYSTEM, generate, render


class RagTests(unittest.TestCase):
    def test_chunk_determinism_and_metadata(self):
        first,_ = make_chunks()
        second,_ = make_chunks()
        self.assertEqual(first,second)
        self.assertEqual(len(first),len({c['chunk_id'] for c in first}))
        for chunk in first:
            self.assertLessEqual(len(chunk['text']),800)
            self.assertTrue({'title','organization','page','canonical_url','language','source_sha256'} <= chunk['metadata'].keys())
            self.assertGreater(chunk['metadata']['page'],0)

    def test_overlap(self):
        text='water '*300
        chunks=list(split_text(text))
        self.assertEqual(chunks[0][1][-120:],chunks[1][1][:120])

    def test_prefixes_and_arabic_tokens(self):
        self.assertEqual(e5_inputs(['مياه']),['passage: مياه'])
        self.assertEqual(e5_inputs(['مياه'],True),['query: مياه'])
        self.assertEqual(tokens('إِدارة  المـياه'),tokens('ادارة المياه'))

    def test_rrf(self):
        result=rrf([{'chunk_id':'a'},{'chunk_id':'b'}],[{'chunk_id':'b'},{'chunk_id':'c'}])
        self.assertEqual(result[0]['chunk_id'],'b')
        self.assertAlmostEqual(result[0]['rrf_score'],1/62+1/61)

    def test_citations_reject_unknown_and_missing(self):
        with self.assertRaises(ValueError):
            render(Answer(insufficient_evidence=False,statements=[Statement(text='Fact',chunk_ids=['invented'])]),[])
        with self.assertRaises(ValueError):
            render(Answer(insufficient_evidence=False,statements=[Statement(text='Fact',chunk_ids=[])]),[])

    def test_grounding_and_empty_context(self):
        self.assertIn('ONLY',SYSTEM)
        self.assertIn('Do not invent unsupported facts',SYSTEM)
        self.assertTrue(generate('Unsupported question',[])['insufficient_evidence'])
        self.assertEqual(generate('Unsupported question',[])['citations'],[])

    def test_numeric_lines_are_not_stitched(self):
        text='المحافظة على المياه والبيئة\n2017\nإدارة الطلب على المياه وتحسين الخدمات'
        runs=list(narrative_runs(text))
        self.assertEqual(len(runs),2)
        self.assertEqual([r[0] for r in runs],[1,3])


if __name__ == '__main__':
    unittest.main(verbosity=2)
