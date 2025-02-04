# gpumon-for-cloudwatch

AWS ECS環境でGPUメトリクスを収集し、CloudWatchに送信するためのサイドカーコンテナです。NVIDIAのGPUメトリクスを定期的に収集し、CloudWatchメトリクスとして保存することで、GPUの使用状況を監視することができます。

## 機能

- GPU使用率の監視
- GPUメモリ使用率の監視
- GPU温度の監視
- GPU電力使用量の監視
- ECSタスクレベルでのメトリクス収集
- CloudWatchへのメトリクス送信
- ローカルログファイルへの記録

## 前提条件

- AWS ECS環境
- NVIDIA GPUを搭載したインスタンス
- 適切なIAMロール（CloudWatchメトリクスの書き込み権限が必要）

## 使用方法

### Dockerイメージのビルド

```bash
docker buildx build --platform linux/x86_64 -t gpumon-for-cloudwatch:latest .
```

### コンテナの実行

```bash
docker run -d \
  --name gpumon-for-cloudwatch \
  --gpus all \
  -e AWS_REGION=<your-aws-region> \
  -e interval=10 \
  -e resolution=60 \
  -e namespace=GPU/Container \
  gpumon-for-cloudwatch:latest
```

### ECS Task Definitionでの設定例

```json
{
  "containerDefinitions": [
    {
      "name": "gpumon",
      "image": "gpumon-for-cloudwatch:latest",
      "essential": true,
      "environment": [
        {
          "name": "interval",
          "value": "10"
        },
        {
          "name": "resolution",
          "value": "60"
        },
        {
          "name": "namespace",
          "value": "GPU/Container"
        }
      ]
    }
  ]
}
```

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|--------------|
| `interval` | メトリクス収集間隔（秒） | 10 |
| `log_path` | ログファイルのパス | /tmp/gpumon_stats |
| `resolution` | CloudWatchメトリクスの解像度（秒） | 60 |
| `namespace` | CloudWatchメトリクスの名前空間 | GPU/Container |

## CloudWatchメトリクス

以下のメトリクスが収集されます：

- `GPU Usage`: GPU使用率（%）
- `Memory Usage`: GPUメモリ使用率（%）
- `Power Usage (Watts)`: 電力使用量（W）
- `Temperature (C)`: GPU温度（℃）

各メトリクスには以下のディメンションが付与されます：
- Cluster: ECSクラスター名
- Service: ECSサービス名

## トラブルシューティング

- コンテナが起動しない場合は、GPUドライバーが正しくインストールされているか確認してください
- CloudWatchにメトリクスが表示されない場合は、IAMロールの権限を確認してください
- ECSタスクのログでエラーメッセージを確認してください

## ライセンス

このプロジェクトはApache License 2.0の下で公開されています。

詳細は[LICENSE](LICENSE)ファイルをご確認ください。

なお、`gpumon.py`は元々Amazon.com, Inc.が作成したコードをベースにしており、そちらもApache License 2.0でライセンスされています。

