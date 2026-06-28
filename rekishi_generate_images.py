#!/usr/bin/env python3
"""
rekishi_generate_images.py
──────────────────────────
74人分の歴史人物デフォルメ画を DALL-E 3 で生成し images/ フォルダに保存します。
Claude Code のターミナルで実行してください。

【使い方】
  1. pip install openai tqdm
  2. export OPENAI_API_KEY="sk-..."
  3. python rekishi_generate_images.py

     # 特定 ID だけ生成したい時
     python rekishi_generate_images.py --ids 1 6 10

     # 既存ファイルをスキップせず上書き
     python rekishi_generate_images.py --overwrite

【出力】
  images/1.png 〜 images/74.png
  ※ HTML 側の IMG_DIR='images/' にするだけで自動表示されます。

【コスト目安】
  DALL-E 3 standard 1024×1024 : $0.04 / 枚
  74枚全部: 約 $2.96（≒ 450 円）
"""

import os, sys, csv, time, argparse, urllib.request
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="*", type=int, help="生成する人物ID（省略時:全員）")
    parser.add_argument("--overwrite", action="store_true", help="既存ファイルも上書き")
    parser.add_argument("--csv", default="figure_prompts.csv", help="プロンプトCSVのパス")
    parser.add_argument("--outdir", default="images", help="出力ディレクトリ")
    parser.add_argument("--size", default="1024x1024", choices=["1024x1024","1024x1792","1792x1024"])
    parser.add_argument("--quality", default="standard", choices=["standard","hd"])
    parser.add_argument("--delay", type=float, default=2.0, help="API 呼び出し間隔（秒）")
    args = parser.parse_args()

    # openai インポート確認
    try:
        from openai import OpenAI
    except ImportError:
        print("❌  openai パッケージが見つかりません。\n   pip install openai tqdm  を実行してください。")
        sys.exit(1)

    # tqdm（プログレスバー）はオプション
    try:
        from tqdm import tqdm
        use_tqdm = True
    except ImportError:
        use_tqdm = False

    # API キー確認
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌  OPENAI_API_KEY が設定されていません。\n   export OPENAI_API_KEY='sk-...'  を実行してください。")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # プロンプト CSV 読み込み
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"❌  {csv_path} が見つかりません。スクリプトと同じディレクトリに置いてください。")
        sys.exit(1)

    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # ID フィルタ
    if args.ids:
        rows = [r for r in rows if int(r["id"]) in args.ids]
        if not rows:
            print("❌  指定した ID が CSV に見つかりません。")
            sys.exit(1)

    out_dir = Path(args.outdir)
    out_dir.mkdir(exist_ok=True)

    print(f"\n🖼️  れきし人物画 生成スタート（{len(rows)} 人）")
    print(f"   出力先 : {out_dir.resolve()}")
    print(f"   品質   : {args.quality}  サイズ: {args.size}")
    unit_cost = 0.04 if args.quality == "standard" else 0.08
    print(f"   目安コスト: ${unit_cost * len(rows):.2f}\n")

    ok = err = skip = 0
    iterator = tqdm(rows, unit="人") if use_tqdm else rows

    for row in iterator:
        fid   = int(row["id"])
        name  = row["name"]
        prompt= row["prompt_en"]
        out_path = out_dir / f"{fid}.png"

        label = f"[{fid:02d}] {name}"
        if not use_tqdm:
            print(f"  処理中 {label} ...", end=" ", flush=True)

        # スキップ判定
        if out_path.exists() and not args.overwrite:
            if not use_tqdm:
                print("スキップ（既存）")
            skip += 1
            continue

        # 生成
        try:
            resp = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=args.size,
                quality=args.quality,
                n=1,
                response_format="url",
            )
            img_url = resp.data[0].url

            # ダウンロード
            urllib.request.urlretrieve(img_url, out_path)

            if not use_tqdm:
                print("✅")
            ok += 1
            time.sleep(args.delay)

        except Exception as e:
            if not use_tqdm:
                print(f"❌ エラー: {e}")
            else:
                tqdm.write(f"  ❌ {label}: {e}")
            err += 1
            time.sleep(args.delay)

    print(f"\n─────────────────────────────")
    print(f"✅ 生成成功: {ok} 人")
    print(f"⏭️  スキップ: {skip} 人（既存ファイル）")
    print(f"❌ エラー  : {err} 人")
    print(f"─────────────────────────────")
    if ok > 0:
        print(f"\n📁 {out_dir}/ に保存されました。")
        print("   クイズ HTML の先頭付近にある")
        print("     const IMG_DIR='';")
        print("   を")
        print("     const IMG_DIR='images/';")
        print("   に変更すると人物画が表示されます。\n")

if __name__ == "__main__":
    main()
