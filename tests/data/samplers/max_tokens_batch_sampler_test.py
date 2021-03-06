from allennlp.common import Params
from allennlp.data import Instance, Token
from allennlp.data.batch import Batch
from allennlp.data.fields import TextField
from allennlp.data.samplers import MaxTokensBatchSampler
from allennlp.data.dataset_readers.dataset_reader import AllennlpDataset
from allennlp.data.dataloader import DataLoader

from .sampler_test import SamplerTest


class TestMaxTokensSampler(SamplerTest):
    def test_create_batches_groups_correctly(self):
        dataset = AllennlpDataset(self.instances, vocab=self.vocab)
        sampler = MaxTokensBatchSampler(
            dataset, max_tokens=8, padding_noise=0, sorting_keys=["text"]
        )

        grouped_instances = []
        for indices in sampler:
            grouped_instances.append([self.instances[idx] for idx in indices])
        expected_groups = [
            [self.instances[4], self.instances[2]],
            [self.instances[0], self.instances[1]],
            [self.instances[3]],
        ]
        for group in grouped_instances:
            assert group in expected_groups
            expected_groups.remove(group)
        assert expected_groups == []

    def test_guess_sorting_key_picks_the_longest_key(self):
        dataset = AllennlpDataset(self.instances, vocab=self.vocab)
        sampler = MaxTokensBatchSampler(dataset, max_tokens=8, padding_noise=0)
        instances = []
        short_tokens = [Token(t) for t in ["what", "is", "this", "?"]]
        long_tokens = [Token(t) for t in ["this", "is", "a", "not", "very", "long", "passage"]]
        instances.append(
            Instance(
                {
                    "question": TextField(short_tokens, self.token_indexers),
                    "passage": TextField(long_tokens, self.token_indexers),
                }
            )
        )
        instances.append(
            Instance(
                {
                    "question": TextField(short_tokens, self.token_indexers),
                    "passage": TextField(long_tokens, self.token_indexers),
                }
            )
        )
        instances.append(
            Instance(
                {
                    "question": TextField(short_tokens, self.token_indexers),
                    "passage": TextField(long_tokens, self.token_indexers),
                }
            )
        )
        assert sampler.sorting_keys is None
        sampler._guess_sorting_keys(instances)
        assert sampler.sorting_keys == ["passage"]

    def test_from_params(self):
        dataset = AllennlpDataset(self.instances, self.vocab)
        params = Params({})

        sorting_keys = ["s1", "s2"]
        params["sorting_keys"] = sorting_keys
        params["max_tokens"] = 32
        sampler = MaxTokensBatchSampler.from_params(params=params, data_source=dataset)

        assert sampler.sorting_keys == sorting_keys
        assert sampler.padding_noise == 0.1
        assert sampler.max_tokens == 32

        params = Params({"sorting_keys": sorting_keys, "padding_noise": 0.5, "max_tokens": 100})

        sampler = MaxTokensBatchSampler.from_params(params=params, data_source=dataset)
        assert sampler.sorting_keys == sorting_keys
        assert sampler.padding_noise == 0.5
        assert sampler.max_tokens == 100

    def test_batch_count(self):
        dataset = AllennlpDataset(self.instances, vocab=self.vocab)
        sampler = MaxTokensBatchSampler(
            dataset, max_tokens=8, padding_noise=0, sorting_keys=["text"]
        )
        # We use a custom collate_fn for testing, which doesn't actually create tensors,
        # just the allennlp Batches.
        dataloader = DataLoader(dataset, batch_sampler=sampler, collate_fn=lambda x: Batch(x))

        assert len(dataloader) == 3
