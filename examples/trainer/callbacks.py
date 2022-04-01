import time

from lumo.core import MetricType
from lumo import Trainer, TrainerParams, callbacks, DataModule, TrainStage


class MyParams(TrainerParams):

    def __init__(self):
        super().__init__()
        self.w = self.SCHE.Cos(1, 0, left=0, right=self.epoch)


params = MyParams()
ParamsType = MyParams


class MyTrainer(Trainer, callbacks.InitialCallback):

    def on_process_loader_begin(self, trainer: 'Trainer', func, params: ParamsType, dm: DataModule, stage: TrainStage,
                                *args, **kwargs):
        super().on_process_loader_begin(trainer, func, params, dm, stage, *args, **kwargs)
        print(loader)

    def icallbacks(self, params: ParamsType):
        super().icallbacks(params)
        callbacks.LoggerCallback(break_in=200).hook(self)
        if isinstance(self, callbacks.BaseCallback):
            self.hook(self)

    def train_step(self, batch, params: ParamsType = None) -> MetricType:
        super().train_step(batch, params)
        res = {'idx': self.global_steps + 0.5, 'w': params.w(self.eidx)}
        # print(res)
        time.sleep(0.05)
        return res


trainer = MyTrainer(params)

from lumo.data import DatasetBuilder

db = (
    DatasetBuilder().add_input('xs', range(100))
        .add_output('xs', 'xs')
)

loader = db.DataLoader(batch_size=10).set_batch_count(40)
trainer.train(loader)
