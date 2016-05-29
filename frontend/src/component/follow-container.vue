<template>
    <div>
        <weibo-follow v-for='keyword in keywords' v-bind:key-word="keyword"></weibo-follow>
    </div>
</template>
<style>
</style>
<script>
    import WeiboFollow from './weibo-follow.vue'
    export default{
        data(){
            return{
                keywords: ['江苏 高考', '南京']
            }
        },
        components:{
            'weibo-follow':WeiboFollow
        }
    }
</script>