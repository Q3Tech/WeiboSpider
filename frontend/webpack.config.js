/**
 * Created by Comzyh on 2016/5/29.
 */
var CopyWebpackPlugin = require('copy-webpack-plugin');
module.exports = {
    entry: './src/app.js',
    output: {
        path: './bin/static',
        publicPath: 'static/',
        filename: 'app.bundle.js',
    },
    module: {
        loaders: [{
            test: /\.vue$/,
            loader: 'vue'
        }, {
            test: /\.js$/,
            loader: 'babel',
            // make sure to exclude 3rd party code in node_modules
            exclude: /node_modules/
        }, {
            test: require.resolve('jquery'),
            loader: 'expose?jQuery'
        }
        ]
    },
    // vue-loader config:
    // lint all JavaScript inside *.vue files with ESLint
    // make sure to adjust your .eslintrc
    vue: {
        loaders: {
            js: 'babel'
        }
    },
    babel: {
        presets: ['es2015'],
        plugins: ['transform-runtime']
    },
    plugins: [
        new CopyWebpackPlugin([
            { from: 'node_modules/bootstrap3/dist/' }
        ])
    ]
}