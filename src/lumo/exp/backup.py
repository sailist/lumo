from .experiment import Experiment
import os
from pprint import pformat
from lumo.utils.fmt import strftime
import re

issue_title = """Test {test_name}"""

summary_template = """
{note}

|Experiment Name|Test Name|Start| End |
|---|---|---|---|
|{exp_name}|{test_name}|{start}|{end}|

```bash
{command}
```

## Parameters
```python
{params}
```

## Metrics

|Key|Value|
|--|--|
{metrics}

Tensor metrics:
```
{non_scalar_metrics}
```

```
{extra_info}
```

## Full properties
<details>
<summary> Click Here </summary>
<code>
{properties}
</code>
</details>
"""


def make_summary(exp: Experiment, **kwargs):
    properties = exp.properties.copy()

    execute = properties['execute']
    params = properties.get('params', {})

    metrics = {}
    non_scalar_metrics = {}
    for k, v in exp.metric.value.items():
        if isinstance(v, (int, float)):
            metrics[k] = f'{v:.5f}'
        else:
            non_scalar_metrics[k] = v
    if len(metrics) == 0:
        metrics['null'] = 'null'

    progress = properties['progress']

    # make markdown string
    working_dir_str = execute['cwd']

    common_prefix = os.path.commonprefix([execute['exec_argv'][0], execute['cwd']])
    file = execute['exec_argv'][0][len(common_prefix):].lstrip('/')
    bin = os.path.basename(execute['exec_bin'])
    command_str = ' '.join(
        [bin, file, *execute['exec_argv'][1:]])
    params_str = pformat(params)
    metrics_str = '\n'.join(f'|{k}|{v}|' for k, v in metrics.items())
    non_scalar_metrics_str = '\n'.join(f'{k}\n{pformat(v)}\n' for k, v in non_scalar_metrics.items())
    properties_str = pformat(properties)

    start_str = progress.get('start', '')
    end_str = progress.get('end', '')
    extra_info_str = '\n'.join(f'{k}: {v}' for k, v in kwargs.items())

    body = summary_template.format(
        # working_dir=working_dir_str,
        exp_name=exp.exp_name,
        note=exp.load_note(),
        test_name=exp.test_name,
        start=start_str,
        end=end_str,
        # interval=interval_str,
        extra_info=extra_info_str,
        command=command_str,
        params=params_str,
        metrics=metrics_str,
        non_scalar_metrics=non_scalar_metrics_str,
        properties=properties_str,
    )

    try:
        username = os.getlogin()
    except OSError:
        pass

    # hide privacy path, only show relative path
    home_with_name = os.path.expanduser('~')
    body = re.sub("""'[^']*\.lumo""", '.lumo', body)
    body = body.replace(home_with_name, '~')

    return body


def backup_github_issue(exp: Experiment, repo: str, access_token: str,
                        labels: list = None, update: bool = True,
                        **kwargs):
    """backup ipath content and bpath content(optional) to github"""
    try:
        from github import Github
    except ImportError as e:
        raise ImportError('backup by github need PyGithub to be installed, try `pip install PyGithub`') from e

    g = Github(login_or_token=access_token)
    repo_obj = g.get_repo(repo)

    title = issue_title.format(test_name=exp.test_name)

    issue = None
    if update:
        number = -1
        old_backup = exp.properties.get('backup', {})
        for k, v in sorted(list(old_backup.items())):
            if v['backend'] == 'github' and v['repo'] == repo:
                number = v['number']

        if number > 0:
            issue = repo_obj.get_issue(number)

    if issue is None:
        issue = repo_obj.create_issue(title=title)
        exp.dump_info('backup', {strftime(): {'backend': 'github', 'number': issue.number, 'repo': repo}}, append=True)

    body = make_summary(exp, **kwargs)

    issue.edit(state='closed', body=body)
    if labels is not None:
        issue.edit(labels=labels)

    return issue

    # There is no way to upload files by GitHub Api
    # filter backuped file sizes
    # files = []
    # for root, dirs, fs in os.walk(exp.mk_ipath()):
    #     for f in fs:
    #         absf = os.path.join(root, f)
    #         file_size = os.path.getsize(absf) / (1024 * 1024)  # Mb
    #         if file_size > size_limit:
    #             continue
    #         files.append(absf)
    #
    # for root, dirs, fs in os.walk(exp.mk_bpath()):
    #     for f in fs:
    #         absf = os.path.join(root, f)
    #         file_size = os.path.getsize(absf) / (1024 * 1024)  # Mb
    #         if file_size > size_limit:
    #             continue
    #         files.append(absf)

    # repo.create_git_blob()
    # {files}
    # issue.create_comment()


def backup_ssh(exp: Experiment, host, username, root, size_limit):
    """compress backup zip files to target server with replacement"""
    pass


def backup_local(exp: Experiment, target):
    pass


backup_regist = {
    'github': backup_github_issue,
    'remote': backup_ssh,
    'local': backup_local,
}
