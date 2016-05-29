<template>
    <div class='weibo-follow'>
        <div class="weibo-follow-header"><b>{{ keyWord }}</b></div>
        <div>
            <weibo-tweet v-for="tweet in tweets" v-bind:tweetp="tweet" v-bind:is_forward="false"></weibo-tweet>
        </div>
    </div>
</template>
<style>
    .weibo-follow {
        float: left;
        padding: 5px 5px;
        margin: 5px 5px;
        box-shadow: 0 0 2px rgba(0,0,0,0.2);
        background-color: rgb(180, 218, 240);
        border-radius: 2px;
    }
    .weibo-follow .weibo-follow-header {
        margin-top: -5px;
        margin-left: -5px;
        margin-right: -5px;
        margin-bottom: 10px;
        padding: 5px;
        background-color: rgb(147, 197, 226);
        border-radius: 2px;
    }
</style>
<script>
    import WeiboTweet from './weibo-tweet.vue'
    var $ = require("jquery")
    export default{
        data(){
            return{
                tweets: []
            }
        },
        props:{
            'keyWord': String
        },
        activate: function (done) {
            var self = this;
            $.getJSON('/api/wordupdate/?word=' + self.keyWord, function(data){
                self.tweets=data;
                done();
            });
        },
        components:{
            'weibo-tweet': WeiboTweet,
        }
    }
</script>