<template>
    <div class="weibo" v-bind:class="{ 'is-forward': is_forward }">
        <b><a href="http://weibo.com/u/{{ tweet.uid }}">{{ tweet.nickname }}</a></b>
        <p>
            <a href="http://weibo.com/{{ tweet.uid}}/{{ tweet.mid }}">{{ tweet.time }}</a>
            <small v-if="tweet.device"> By {{ tweet.device }}</small>
            <small v-if="tweet.location"> @ {{ tweet.location }}</small>
        </p>
        <p>{{ tweet.text }}</p>
        <weibo-tweet v-if="tweet.forward_tweet" v-bind:tweetp="tweet.forward_tweet" v-bind:is_forward="true"></weibo-tweet>
        <div class="weibo-handle">
            <ul class="clearfix">
                <li>转发 {{ tweet.share }}</li>
                <li>评论 {{ tweet.comment }}</li>
                <li>赞 {{ tweet.like }}</li>
            </ul>
        </div>
    </div>
</template>
<style>
    .weibo-transition {
        transition: opacity .5s ease;
    }
    .weibo-move {
        transition: transform 1.5s cubic-bezier(.55,0,.1,1);
    }
    .weibo-enter {
        opacity: 0;
    }
    .weibo {
        font-size: 14px;
        font-family: Arial, 'Microsoft YaHei';
        max-width: 500px;
        margin-bottom: 10px;
    }
    .weibo:not(.is-forward){
        padding: 5px 5px;
        box-shadow: 0 0 2px rgba(0,0,0,0.2);
        border-radius: 2px;
        background: #FFF;
    }
    .weibo.is-forward {
        font-size: 12px;
        padding-left: 15px;
        padding-top: 5px;
        padding-bottom: 5px;
        margin-left: -5px;
        margin-right: -5px;
        background-color: #F2F2F5;
        margin-bottom: 0;
    }
    .weibo p {
        margin-top: 0;
        margin-bottom: 5px;
    }
    .weibo a {
        color: #333;
        text-decoration: none;
    }
    .weibo a:hover {
        color: #337ab7;
    }
    .weibo:not(.is-forward) .weibo-handle {
        margin: 0 -5px 0 -5px;
    }
    .weibo .weibo-handle ul{
        margin: 0;
        padding: 0;
        width: 100%;
    }
    .weibo.is-forward .weibo-handle ul{
        padding-left: 50%;
    }
    .weibo .weibo-handle li{
        width: 33%;
        display: list-item;
        float: left;
        /*border-left: #d9d9d9 1px solid;*/
        text-align: center;
    }
</style>
<script>
//    import HeaderComponent from './components/header.vue'
//    import OtherComponent from './components/other.vue'
    var dateFormat = require('dateformat');
    export default{
        data(){
            return{
            }
        },
        props: ['tweetp', 'is_forward'],
        computed: {
            tweet: function () {
                var tp = this.tweetp;
                return {
                    'uid': tp.uid,
                    'mid': tp.mid,
                    'nickname': tp.nickname,
                    'text': tp.text,
                    'time': dateFormat(new Date(tp.timestamp), "yyyy-mm-dd HH:MM:ss"),
                    'device': tp.device,
                    'share': tp.share,
                    'comment': tp.comment,
                    'like': tp.like,
                    'forward_tweet': tp.forward_tweet
                }
            }
        },
        name: 'weibo-tweet'
    }
</script>