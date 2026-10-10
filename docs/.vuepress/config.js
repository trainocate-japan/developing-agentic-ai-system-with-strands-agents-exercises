import { viteBundler } from '@vuepress/bundler-vite'
import { defaultTheme } from '@vuepress/theme-default'
import { defineUserConfig } from 'vuepress'

export default defineUserConfig({
  lang: 'ja-JP',
  title: 'Agentic AI 開発実践 - Strands Agents 版',
  description: '演習ガイド',

  // GitHub Pagesでのプロジェクトページ公開を想定したbase path。
  // リポジトリ名・公開先が変わる場合はここを合わせて変更してください。
  base: '/developing-agentic-ai-system-with-strands-agents-exercises/',

  bundler: viteBundler(),

  theme: defaultTheme({
    contributors: false,
    navbar: [
      { text: 'ホーム', link: '/' },
      { text: '演習ガイド', link: '/guide/' },
    ],
    sidebar: {
      '/guide/': [
        '/guide/module3/exercise1.md',
        '/guide/module4/exercise2.md',
        '/guide/module5/exercise3.md',
        '/guide/module6/exercise4.md',
        '/guide/module7/exercise5.md',
        '/guide/module8/exercise6.md',
      ],
    },
  }),
})
