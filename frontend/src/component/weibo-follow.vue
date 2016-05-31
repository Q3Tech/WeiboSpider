<template>
    <div class='weibo-follow'>
        <div class="weibo-follow-header">
            <b>{{ keyWord }}</b>
            <button type="button" class="close" v-on:click="close">×</button>
        </div>
        <div style="height: 100%;">
            <div class="scroll">
                <div>
                    <div v-for="tweet in tweets" transition="weibo" track-by="mid">
                        <weibo-tweet  v-bind:tweetp="tweet" v-bind:is_forward="false"  class="weibo"></weibo-tweet>
                    </div>

                </div>
            </div>
        </div>
    </div>
</template>
<style>
    .weibo-follow {
        position: relative;
        white-space: initial;
        display: inline-block;
        padding-top: 35px;
        padding-bottom: 3px;
        margin-left: 5px;
        box-shadow: 0 0 2px rgba(0,0,0,0.2);
        background-color: rgb(180, 218, 240);
        border-radius: 2px;
        height: 100%;
        min-width: 505px;
    }
    .weibo-follow .scroll {
        overflow-x: hidden;
        overflow-y: auto;
        height:100%;
        padding-left: 5px;
        /*padding-right: 5px;*/
    }
    .weibo-follow .weibo-follow-header {
        margin-bottom: 10px;
        padding: 5px;
        background-color: rgb(147, 197, 226);
        border-radius: 2px;
        position: absolute;
        left:0px;
        right:0px;
        top:0px;
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
        },
        methods: {
            close:function () {
                this.$dispatch('container-remove-keyword', this.keyWord);
            }
        },
        events:{
            'wordfollow-update': function (word, tweets) {
                if (word != this.keyWord){
                    return
                }
                for(var i = tweets.length - 1; i >= 0; i--){
                    this.tweets.unshift(tweets[i]);
                }
            }
        }
    }
</script>