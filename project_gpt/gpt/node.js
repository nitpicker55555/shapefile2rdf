import dotenv from 'dotenv'
import http from 'node:http'
import { Readable } from 'node:stream'
import url from 'node:url'
import { Configuration, OpenAIApi } from "openai"

dotenv.config()

const configuration = new Configuration({
    organization: process.env.OPENAI_API_ORGANIZATION,
    apiKey: process.env.OPENAI_API_KEY,
})
const openai = new OpenAIApi(configuration)

const server = http.createServer((req, res) => {
    const { pathname } = url.parse(req.url || '/')

    if (req.method === 'OPTIONS') {
        res.setHeader('Access-Control-Allow-Origin', '*')
        res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
        res.end()
    } else if (req.method === 'POST' && pathname === '/chatgpt') {
        let body = ''
        req.on('data', (chunk) => {
            body += chunk
        })

        req.on('end', async () => {
            const { messages } = JSON.parse(body)
            // Set the response headers
            res.setHeader('Access-Control-Allow-Origin', '*')
            res.setHeader("Content-Type", "text/event-stream; charset=utf-8")
            res.setHeader("Cache-Control", "no-cache")
            res.setHeader("Connection", "keep-alive")

            const streamResponse = await openai.createChatCompletion({
                model: "gpt-3.5-turbo",
                stream: true,
                messages: messages
            }, { responseType: 'stream' })


            // Convert the response to a Readable stream (this is a temporary workaround)
            const stream = streamResponse.data
            stream.on('data', chunk => {
                res.write(chunk)
            })

            stream.on('end', () => {
                res.end()
            })
        })
    } else {
        res.statusCode = 404
        res.end()
    }
})

server.listen(65532, '0.0.0.0', () => {
    console.log('Server listening on port 65532')
})