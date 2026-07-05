from typing import Dict, Any, Tuple
from ...contracts import Archetype, Channel, Emotion, Industry

# The playbook maps (emotion, industry) -> marketing archetype and generated template details.
# Emotion is a value from the Emotion enum.
# Industry is a value from the Industry enum.
# A key of ("*", industry) serves as a fallback for any unmatched emotion for that industry.
# A key of ("*", "*") serves as a global fallback.

PLAYBOOK: Dict[Tuple[str, str], Dict[str, Any]] = {
    # ---------------------------------------------------------
    # 1. FOOD DELIVERY (Match-watching = peak ordering; goal spikes → moment-timed flash offers)
    # ---------------------------------------------------------
    (Emotion.joy.value, Industry.food_delivery.value): {
        "archetype": Archetype.celebration_flash_offer,
        "window_minutes": 15,
        "channel_default": Channel.push,
        "tone_notes": "High energy, celebratory. Focus on rewarding the hype with immediate food discounts. Use pizza/burger/beer emojis.",
        "template": {
            "headline": "GOOOOOOAL! Fuel the Celebration! 🍕🔥",
            "body": "Your team just scored! Keep the energy high with 25% off your next order. Valid for the next {window_minutes} mins.",
            "cta": "Claim 25% Off",
            "hashtags": ["#{match_hashtag}", "#MatchDayFeast"],
            "variant_b": {
                "headline": "Goal Hype = Pizza Time! 🍔",
                "body": "Celebrate that insane moment! Enjoy a 25% flash discount on all {segment_favorite} deliveries.",
                "cta": "Order Now"
            }
        }
    },
    (Emotion.sadness.value, Industry.food_delivery.value): {
        "archetype": Archetype.consolation_offer,
        "window_minutes": 30,
        "channel_default": Channel.push,
        "tone_notes": "Empathetic, comforting. Acknowledge the tough moment and offer comfort food as a remedy.",
        "template": {
            "headline": "Rough moment? Comfort food helps. 🍔",
            "body": "We feel it too. Take the edge off with free delivery on all orders for the next {window_minutes} mins.",
            "cta": "Get Comfort Food",
            "hashtags": ["#{match_hashtag}", "#ComfortFood"],
            "variant_b": {
                "headline": "Cheer up with a free treat 🍦",
                "body": "Tough break for the team. Let us cheer you up—free dessert with any order right now.",
                "cta": "Order Comfort"
            }
        }
    },
    (Emotion.anger.value, Industry.food_delivery.value): {
        "archetype": Archetype.consolation_offer,
        "window_minutes": 20,
        "channel_default": Channel.push,
        "tone_notes": "Understanding the frustration. Position food as the perfect distraction.",
        "template": {
            "headline": "Frustrated? Eat it off. 🌮",
            "body": "That call was unbelievable. Cool down with 20% off your next order.",
            "cta": "Cool Down Now",
            "hashtags": ["#{match_hashtag}", "#SnackRelief"],
            "variant_b": {
                "headline": "Don't let it ruin your night 🍕",
                "body": "Take a breather. Grab your favorite meal with a 20% flash discount.",
                "cta": "Order Now"
            }
        }
    },
    (Emotion.surprise.value, Industry.food_delivery.value): {
        "archetype": Archetype.celebration_flash_offer,
        "window_minutes": 15,
        "channel_default": Channel.push,
        "tone_notes": "Shocked, hyped! Capitalize on the unexpected twist in the match.",
        "template": {
            "headline": "Did that just happen?! 🤯",
            "body": "What a twist! Celebrate the shocker with 20% off all fast-food deliveries.",
            "cta": "Claim Discount",
            "hashtags": ["#{match_hashtag}", "#MatchShock"],
            "variant_b": {
                "headline": "Unbelievable scenes! 🍟",
                "body": "We can't believe it either. Grab a quick bite with this surprise 20% off code.",
                "cta": "Order Quick"
            }
        }
    },
    (Emotion.fear.value, Industry.food_delivery.value): {
        "archetype": Archetype.consolation_offer,
        "window_minutes": 30,
        "channel_default": Channel.push,
        "tone_notes": "Tense, anxious. Position the offer as stress-eating relief during a nail-biting match.",
        "template": {
            "headline": "Nerve-wracking match? 😬",
            "body": "Stress-eat your way through the final minutes. Free delivery on all orders right now.",
            "cta": "Order Relief",
            "hashtags": ["#{match_hashtag}", "#NailBiter"],
            "variant_b": {
                "headline": "Can't watch? Just eat. 🍔",
                "body": "Relieve the tension with your favorite snacks. Free delivery for {window_minutes} mins.",
                "cta": "Get Snacks"
            }
        }
    },
    (Emotion.disgust.value, Industry.food_delivery.value): {
        "archetype": Archetype.consolation_offer,
        "window_minutes": 30,
        "channel_default": Channel.push,
        "tone_notes": "Validating the bad taste left by the match. Offer a literal good taste.",
        "template": {
            "headline": "Wash that bad taste away 🥤",
            "body": "Terrible moment on the pitch. Let us make it better with 20% off all drinks and sides.",
            "cta": "Order Now",
            "hashtags": ["#{match_hashtag}", "#MatchDay"],
            "variant_b": {
                "headline": "Need a distraction? 🍟",
                "body": "Look away from the screen and look at this deal: 20% off your next delivery.",
                "cta": "Distract Me"
            }
        }
    },
    (Emotion.neutral.value, Industry.food_delivery.value): {
        "archetype": Archetype.watch_it_here,
        "window_minutes": 60,
        "channel_default": Channel.push,
        "tone_notes": "Standard match-day hype. Remind them to order food before the climax.",
        "template": {
            "headline": "Half-time hunger? 🍕",
            "body": "Stock up on snacks before the match heats up. 15% off all orders over $25.",
            "cta": "Order Snacks",
            "hashtags": ["#{match_hashtag}", "#HalfTime"],
            "variant_b": {
                "headline": "Fuel up for the second half 🍔",
                "body": "Don't miss a minute. Order now and get it delivered before the whistle blows.",
                "cta": "Pre-order"
            }
        }
    },

    # ---------------------------------------------------------
    # 2. MERCH & APPAREL (Wins drive impulse buys → "commemorate the moment" drops)
    # ---------------------------------------------------------
    (Emotion.joy.value, Industry.merch_apparel.value): {
        "archetype": Archetype.commemorative_drop,
        "window_minutes": 60,
        "channel_default": Channel.instagram,
        "tone_notes": "Hype, exclusivity. Frame the merch as a way to own a piece of this historic moment.",
        "template": {
            "headline": "Own The Moment! 🏆👕",
            "body": "What a historic strike! The limited edition '{trending_topic}' commemorative tees just dropped.",
            "cta": "Shop The Drop",
            "hashtags": ["#{match_hashtag}", "#LimitedEdition"],
            "variant_b": {
                "headline": "Instant Classic. Get the Gear! 🔥",
                "body": "Celebrate the victory with our exclusive match-day apparel. Only available for the next hour.",
                "cta": "Grab Yours"
            }
        }
    },
    (Emotion.surprise.value, Industry.merch_apparel.value): {
        "archetype": Archetype.commemorative_drop,
        "window_minutes": 60,
        "channel_default": Channel.instagram,
        "tone_notes": "Reactive, fast. Highlighting the shocking twist with related gear.",
        "template": {
            "headline": "Unbelievable! Commemorate it. 🤯👕",
            "body": "Nobody saw that coming. Get the exclusive '{trending_topic}' upset tee before it sells out.",
            "cta": "Shop Now",
            "hashtags": ["#{match_hashtag}", "#ShockUpset"],
            "variant_b": {
                "headline": "The Underdog Story 💥",
                "body": "Support the surprise stars of the match. Fresh jerseys restocked!",
                "cta": "Get The Jersey"
            }
        }
    },
    (Emotion.sadness.value, Industry.merch_apparel.value): {
        "archetype": Archetype.brand_awareness,
        "window_minutes": 120,
        "channel_default": Channel.instagram,
        "tone_notes": "Loyalty, pride. Emphasize standing by the team through thick and thin.",
        "template": {
            "headline": "True fans stay loyal. 💙",
            "body": "Through the highs and lows, wear your colors with pride. Team scarves now 20% off.",
            "cta": "Show Your Pride",
            "hashtags": ["#{match_hashtag}", "#TrueFans"],
            "variant_b": {
                "headline": "Always behind the team 🛡️",
                "body": "Tough result, but the passion never dies. Shop the official supporter collection.",
                "cta": "Shop Collection"
            }
        }
    },
    (Emotion.anger.value, Industry.merch_apparel.value): {
        "archetype": Archetype.brand_awareness,
        "window_minutes": 60,
        "channel_default": Channel.instagram,
        "tone_notes": "Defiant, passionate. Channel the anger into team pride.",
        "template": {
            "headline": "Us Against The World 😤",
            "body": "Show them we won't back down. Gear up in the latest official away kit.",
            "cta": "Gear Up",
            "hashtags": ["#{match_hashtag}", "#DefiantPride"],
            "variant_b": {
                "headline": "Fuel the fire 🔥",
                "body": "Channel the passion. Wear the crest with pride.",
                "cta": "Shop Kits"
            }
        }
    },
    (Emotion.fear.value, Industry.merch_apparel.value): {
        "archetype": Archetype.brand_awareness,
        "window_minutes": 120,
        "channel_default": Channel.instagram,
        "tone_notes": "Nervous excitement. Focus on lucky charms or protective gear.",
        "template": {
            "headline": "Need some luck? 🍀",
            "body": "It's getting tense. Grab your lucky team scarf for the final whistle.",
            "cta": "Get Lucky Gear",
            "hashtags": ["#{match_hashtag}", "#LuckyScarf"],
            "variant_b": {
                "headline": "Hold the line 🛡️",
                "body": "Stand strong with the team. Shop the defender collection.",
                "cta": "Shop Now"
            }
        }
    },
    (Emotion.disgust.value, Industry.merch_apparel.value): {
        "archetype": Archetype.brand_awareness,
        "window_minutes": 120,
        "channel_default": Channel.instagram,
        "tone_notes": "Focus on the purity of the sport and classic team heritage.",
        "template": {
            "headline": "Back to the classics ⚽",
            "body": "Remember the good old days. Shop our retro jersey collection.",
            "cta": "Shop Retro",
            "hashtags": ["#{match_hashtag}", "#RetroKits"],
            "variant_b": {
                "headline": "Pure passion 💙",
                "body": "Strip away the drama. Just pure team pride. View the essential collection.",
                "cta": "View Essentials"
            }
        }
    },
    (Emotion.neutral.value, Industry.merch_apparel.value): {
        "archetype": Archetype.brand_awareness,
        "window_minutes": 120,
        "channel_default": Channel.instagram,
        "tone_notes": "Casual, stylish. Focus on lifestyle and streetwear.",
        "template": {
            "headline": "Match Day Style 👕",
            "body": "Looking good for the big game. Check out our new streetwear collection.",
            "cta": "Shop Style",
            "hashtags": ["#{match_hashtag}", "#MatchDayFit"],
            "variant_b": {
                "headline": "Represent your city 🏙️",
                "body": "Show off your local pride with our city-edition apparel.",
                "cta": "Shop City Edition"
            }
        }
    },

    # ---------------------------------------------------------
    # 3. BEVERAGES (Core watch-along consumption)
    # ---------------------------------------------------------
    (Emotion.joy.value, Industry.beverages.value): {
        "archetype": Archetype.celebration_flash_offer,
        "window_minutes": 20,
        "channel_default": Channel.push,
        "tone_notes": "Cheers! Popping bottles, celebrating with a cold one.",
        "template": {
            "headline": "Cheers to that GOAL! 🍻",
            "body": "Celebrate the moment with a cold one. 20% off your next 6-pack delivery.",
            "cta": "Order Drinks",
            "hashtags": ["#{match_hashtag}", "#Cheers"],
            "variant_b": {
                "headline": "Pop the bottles! 🍾",
                "body": "What a strike! Celebrate with instant beverage delivery.",
                "cta": "Celebrate Now"
            }
        }
    },
    (Emotion.sadness.value, Industry.beverages.value): {
        "archetype": Archetype.consolation_offer,
        "window_minutes": 30,
        "channel_default": Channel.push,
        "tone_notes": "Sympathetic. Drowning sorrows with a comforting drink.",
        "template": {
            "headline": "Need a pick-me-up? ☕",
            "body": "Rough match. Comfort yourself with a hot drink, delivered fast.",
            "cta": "Order Now",
            "hashtags": ["#{match_hashtag}", "#ComfortDrink"],
            "variant_b": {
                "headline": "Next time 🍻",
                "body": "We go again next week. Grab a cold one to ease the pain.",
                "cta": "Order Drinks"
            }
        }
    },
    (Emotion.anger.value, Industry.beverages.value): {
        "archetype": Archetype.consolation_offer,
        "window_minutes": 30,
        "channel_default": Channel.push,
        "tone_notes": "Cooling down. Offering a refreshing drink to ease the heat of the moment.",
        "template": {
            "headline": "Cool down. 🧊",
            "body": "That referee call was wild. Cool off with an icy refreshment.",
            "cta": "Get Refreshments",
            "hashtags": ["#{match_hashtag}", "#CoolDown"],
            "variant_b": {
                "headline": "Take a breath 🥤",
                "body": "Sip and relax. 15% off all cold beverages right now.",
                "cta": "Relax Now"
            }
        }
    },
    (Emotion.surprise.value, Industry.beverages.value): {
        "archetype": Archetype.celebration_flash_offer,
        "window_minutes": 20,
        "channel_default": Channel.push,
        "tone_notes": "Shocked, hyped. Need a drink to process what just happened.",
        "template": {
            "headline": "Did you see that?! 🤯🍻",
            "body": "Unbelievable scenes! Toast to the surprise with 20% off drinks.",
            "cta": "Toast Now",
            "hashtags": ["#{match_hashtag}", "#MatchShock"],
            "variant_b": {
                "headline": "Speechless 🙊🍹",
                "body": "Process that crazy moment with your favorite beverage.",
                "cta": "Order Drinks"
            }
        }
    },
    (Emotion.fear.value, Industry.beverages.value): {
        "archetype": Archetype.brand_awareness,
        "window_minutes": 60,
        "channel_default": Channel.push,
        "tone_notes": "Tense. Need a drink to settle the nerves.",
        "template": {
            "headline": "Nerves of steel 🧊",
            "body": "Settle those match-day nerves with a cold, refreshing drink.",
            "cta": "Order Now",
            "hashtags": ["#{match_hashtag}", "#TenseMatch"],
            "variant_b": {
                "headline": "Hold your breath 🍺",
                "body": "It's going down to the wire. Make sure your glass is full.",
                "cta": "Refill Glass"
            }
        }
    },
    (Emotion.disgust.value, Industry.beverages.value): {
        "archetype": Archetype.consolation_offer,
        "window_minutes": 30,
        "channel_default": Channel.push,
        "tone_notes": "Wash the bad taste away.",
        "template": {
            "headline": "Wash it away 🥤",
            "body": "Bad moment on the pitch. Wash it down with your favorite soda.",
            "cta": "Order Soda",
            "hashtags": ["#{match_hashtag}", "#Refresh"],
            "variant_b": {
                "headline": "Clean slate 🧊",
                "body": "Let's forget that happened. Refresh yourself with 15% off drinks.",
                "cta": "Refresh Now"
            }
        }
    },
    (Emotion.neutral.value, Industry.beverages.value): {
        "archetype": Archetype.watch_it_here,
        "window_minutes": 60,
        "channel_default": Channel.instagram,
        "tone_notes": "Casual watch-along vibes.",
        "template": {
            "headline": "Perfect Match Companion 🍻",
            "body": "Watching the game? Make sure you've got your favorite beverages stocked.",
            "cta": "Stock Up",
            "hashtags": ["#{match_hashtag}", "#MatchDayDrinks"],
            "variant_b": {
                "headline": "Thirsty? 🥤",
                "body": "Don't pause the match. Get drinks delivered in under 30 mins.",
                "cta": "Order Delivery"
            }
        }
    },

    # ---------------------------------------------------------
    # 4. STREAMING OTT (Pre-match tune-in / highlight clips)
    # ---------------------------------------------------------
    (Emotion.joy.value, Industry.streaming_ott.value): {
        "archetype": Archetype.tune_in_push,
        "window_minutes": 10,
        "channel_default": Channel.push,
        "tone_notes": "FOMO, excitement. Emphasize that history is being made right now.",
        "template": {
            "headline": "Are you watching this?! 📺🔥",
            "body": "An incredible goal just happened! Tune in live on our app to catch the rest of this classic.",
            "cta": "Watch Live",
            "hashtags": ["#{match_hashtag}", "#LiveSports"],
            "variant_b": {
                "headline": "Don't miss out! ⚽",
                "body": "The stadium is rocking! Stream the second half live right now.",
                "cta": "Stream Now"
            }
        }
    },
    (Emotion.sadness.value, Industry.streaming_ott.value): {
        "archetype": Archetype.brand_awareness,
        "window_minutes": 60,
        "channel_default": Channel.email,
        "tone_notes": "Reflective. Watch the post-match analysis.",
        "template": {
            "headline": "What went wrong? 📺",
            "body": "Heartbreak on the pitch. Tune in for the exclusive post-match tactical breakdown.",
            "cta": "Watch Analysis",
            "hashtags": ["#{match_hashtag}", "#PostMatch"],
            "variant_b": {
                "headline": "The Aftermath ⚽",
                "body": "Hear directly from the manager in our live post-match press conference stream.",
                "cta": "Watch Presser"
            }
        }
    },
    (Emotion.anger.value, Industry.streaming_ott.value): {
        "archetype": Archetype.tune_in_push,
        "window_minutes": 15,
        "channel_default": Channel.push,
        "tone_notes": "Controversial. Hook them with the drama.",
        "template": {
            "headline": "Did the ref get it wrong? 🤬📺",
            "body": "Huge controversy on the pitch! Watch the replay from all angles live on our app.",
            "cta": "Watch Replay",
            "hashtags": ["#{match_hashtag}", "#VAR"],
            "variant_b": {
                "headline": "Absolute Drama! 🤯",
                "body": "Things are heating up. Don't miss a second of this intense matchup.",
                "cta": "Watch Live"
            }
        }
    },
    (Emotion.surprise.value, Industry.streaming_ott.value): {
        "archetype": Archetype.tune_in_push,
        "window_minutes": 10,
        "channel_default": Channel.push,
        "tone_notes": "Urgent FOMO. You have to see this to believe it.",
        "template": {
            "headline": "SHOCKER! Tune in now! 😱📺",
            "body": "The biggest upset of the tournament is happening right now. Stream it live!",
            "cta": "Watch Live",
            "hashtags": ["#{match_hashtag}", "#UpsetAlert"],
            "variant_b": {
                "headline": "You won't believe this 🤯",
                "body": "Madness on the pitch! Jump into the live stream before it's over.",
                "cta": "Stream Now"
            }
        }
    },
    (Emotion.fear.value, Industry.streaming_ott.value): {
        "archetype": Archetype.tune_in_push,
        "window_minutes": 15,
        "channel_default": Channel.push,
        "tone_notes": "Suspense. It's going down to the wire.",
        "template": {
            "headline": "Down to the wire! 😬📺",
            "body": "A nail-biting finish is guaranteed. Tune in for the final 10 minutes live!",
            "cta": "Watch Finale",
            "hashtags": ["#{match_hashtag}", "#TenseFinish"],
            "variant_b": {
                "headline": "Can they hold on? 🛡️",
                "body": "It's all out attack! Watch the dramatic conclusion live on our app.",
                "cta": "Watch Live"
            }
        }
    },
    (Emotion.disgust.value, Industry.streaming_ott.value): {
        "archetype": Archetype.tune_in_push,
        "window_minutes": 15,
        "channel_default": Channel.push,
        "tone_notes": "Drama. See the controversial moment for yourself.",
        "template": {
            "headline": "See it to believe it 📺",
            "body": "A shocking moment has everyone talking. Catch the replay and live analysis now.",
            "cta": "Watch Analysis",
            "hashtags": ["#{match_hashtag}", "#MatchDrama"],
            "variant_b": {
                "headline": "What just happened? 🤷",
                "body": "Dive into the live debate on our post-match show.",
                "cta": "Watch Debate"
            }
        }
    },
    (Emotion.neutral.value, Industry.streaming_ott.value): {
        "archetype": Archetype.tune_in_push,
        "window_minutes": 60,
        "channel_default": Channel.push,
        "tone_notes": "Anticipation. Pre-match or half-time push.",
        "template": {
            "headline": "Kickoff approaching! ⚽📺",
            "body": "The teams are in the tunnel. Stream the big match live in high definition.",
            "cta": "Watch Live",
            "hashtags": ["#{match_hashtag}", "#LiveFootball"],
            "variant_b": {
                "headline": "Second half starting soon ⏱️",
                "body": "Don't miss the tactical changes. Tune back in for the second half.",
                "cta": "Resume Stream"
            }
        }
    },

    # ---------------------------------------------------------
    # 5. CONTENT CREATOR (Attention monetization)
    # ---------------------------------------------------------
    (Emotion.joy.value, Industry.content_creator.value): {
        "archetype": Archetype.content_idea,
        "window_minutes": 15,
        "channel_default": Channel.youtube,
        "tone_notes": "Hype reaction video. Pure excitement and celebration.",
        "template": {
            "format": "YouTube Shorts / Reels",
            "hook": "Scream at the camera when {trending_topic} scores!",
            "concept": "Record a raw, unfiltered reaction to the goal. Show your pure joy and break down the build-up play in 30 seconds.",
            "hashtags": ["#{match_hashtag}", "#GoalReaction"],
            "post_within_minutes": 20
        }
    },
    (Emotion.sadness.value, Industry.content_creator.value): {
        "archetype": Archetype.content_idea,
        "window_minutes": 30,
        "channel_default": Channel.youtube,
        "tone_notes": "Somber analysis. Empathetic rant.",
        "template": {
            "format": "Long-form YouTube video",
            "hook": "'Where did it all go wrong for the team today?'",
            "concept": "A sit-down, emotional review of the match. Discuss {trending_topic} and the tactical failures that led to the loss.",
            "hashtags": ["#{match_hashtag}", "#MatchReview"],
            "post_within_minutes": 120
        }
    },
    (Emotion.anger.value, Industry.content_creator.value): {
        "archetype": Archetype.content_idea,
        "window_minutes": 15,
        "channel_default": Channel.youtube,
        "tone_notes": "Passionate rant. Calling out the referee or the players.",
        "template": {
            "format": "TikTok / YouTube Shorts",
            "hook": "'I can't believe the referee just did that!'",
            "concept": "A passionate, high-energy rant about the controversial decision involving {trending_topic}. Ask viewers for their opinion in the comments.",
            "hashtags": ["#{match_hashtag}", "#FootballDebate"],
            "post_within_minutes": 15
        }
    },
    (Emotion.surprise.value, Industry.content_creator.value): {
        "archetype": Archetype.content_idea,
        "window_minutes": 15,
        "channel_default": Channel.youtube,
        "tone_notes": "Mind blown. Focus on the unpredictability.",
        "template": {
            "format": "Reaction video clip",
            "hook": "Hold your head in your hands in disbelief.",
            "concept": "React to the insane upset! Talk about how {trending_topic} just changed the entire tournament bracket.",
            "hashtags": ["#{match_hashtag}", "#Upset"],
            "post_within_minutes": 30
        }
    },
    (Emotion.fear.value, Industry.content_creator.value): {
        "archetype": Archetype.content_idea,
        "window_minutes": 20,
        "channel_default": Channel.youtube,
        "tone_notes": "Anxious watch-along. Biting nails.",
        "template": {
            "format": "Live stream highlight",
            "hook": "'This is too tense to watch!'",
            "concept": "Clip your live stream reaction during the final 5 minutes. Highlight the defensive plays by {trending_topic}.",
            "hashtags": ["#{match_hashtag}", "#TenseMoments"],
            "post_within_minutes": 45
        }
    },
    (Emotion.disgust.value, Industry.content_creator.value): {
        "archetype": Archetype.content_idea,
        "window_minutes": 30,
        "channel_default": Channel.youtube,
        "tone_notes": "Critical breakdown. Calling out bad behavior or poor tactics.",
        "template": {
            "format": "Tactical breakdown",
            "hook": "'This is exactly what is ruining the game.'",
            "concept": "A critical analysis of the poor sportsmanship or terrible tactical setup involving {trending_topic}.",
            "hashtags": ["#{match_hashtag}", "#TacticalAnalysis"],
            "post_within_minutes": 60
        }
    },
    (Emotion.neutral.value, Industry.content_creator.value): {
        "archetype": Archetype.content_idea,
        "window_minutes": 120,
        "channel_default": Channel.youtube,
        "tone_notes": "Educational, informative preview.",
        "template": {
            "format": "Match Preview",
            "hook": "'Here are 3 things to look out for in today's match.'",
            "concept": "A statistical preview focusing on {trending_topic} and key matchups on the pitch.",
            "hashtags": ["#{match_hashtag}", "#MatchPreview"],
            "post_within_minutes": 120
        }
    },
}

# Add fallback rows for all other un-starred industries
for ind in Industry:
    if ind.value not in [Industry.food_delivery.value, Industry.merch_apparel.value, Industry.beverages.value, Industry.streaming_ott.value, Industry.content_creator.value]:
        PLAYBOOK[("*", ind.value)] = {
            "archetype": Archetype.brand_awareness,
            "window_minutes": 120,
            "channel_default": Channel.instagram,
            "tone_notes": "General brand awareness tied to the match excitement. Keep it light and engaging.",
            "template": {
                "headline": "Loving the match? ⚽",
                "body": "We are too! Celebrate match day with our latest collection.",
                "cta": "Explore Now",
                "hashtags": ["#{match_hashtag}", "#MatchDay"],
                "variant_b": {
                    "headline": "Game On! 🏆",
                    "body": "Elevate your match day experience with us.",
                    "cta": "Learn More"
                }
            }
        }

# Global fallback just in case
PLAYBOOK[("*", "*")] = {
    "archetype": Archetype.brand_awareness,
    "window_minutes": 120,
    "channel_default": Channel.instagram,
    "tone_notes": "Neutral brand awareness.",
    "template": {
        "headline": "Enjoying the game? ⚽",
        "body": "Check out our latest offerings while you watch.",
        "cta": "Shop Now",
        "hashtags": ["#{match_hashtag}", "#MatchDay"],
        "variant_b": {
            "headline": "Match Day Special 🌟",
            "body": "Discover what's new today.",
            "cta": "Discover"
        }
    }
}
