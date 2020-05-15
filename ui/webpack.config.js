const path = require('path');
const webpack = require('webpack');


module.exports = {
    entry: {
        odinlib: './src/js/index'
    },
    output: {
        path: path.join(__dirname, "dist"),
        filename: "[name].js",
        library: ["[name]"],
        libraryTarget: "umd"
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                },
            },
            {
                test: /\.json$/,
                loader: 'json-loader',
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader'],
            },
            {
                test: /\.html$/,
                use: {
                    loader: 'file-loader',
                    options: { name: '[name].[ext]' },
                },
            },
            {
                test: /\.(woff|woff2|eot|ttf|otf|svg|png)$/,
                use: ['file-loader'],
            },
            {
                test: /\.gif$/,
                use: ['file-loader'],
            },
        ],
    },
    plugins: [
        new webpack.ProvidePlugin({
           $: "jquery",
           jQuery: "jquery"
       })
    ]
};
